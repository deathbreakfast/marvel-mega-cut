import os
import sys
import time
import threading
from typing import Dict, List, Optional
from datetime import datetime
from progress_tracker import ProgressTracker
from logger import ProgressLogger

# Rich library for static displays only
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from tqdm import tqdm

class ProgressUI:
    """
    UI display system for Marvel Mega Cut processing.
    Uses tqdm for progress bars and rich for static displays.
    """
    
    def __init__(self, logger: ProgressLogger, tracker: ProgressTracker, debug=False):
        self.logger = logger
        self.tracker = tracker
        self.console = Console()
        self.static_content_shown = False
        self.debug = debug
        
        # Progress display state
        self.progress_started = False
        self.current_pbar = None
        self.current_chunk = None
        
        # Threading for UI updates
        self.ui_thread = None
        self.ui_running = False
        self.ui_lock = threading.Lock()
    
    def start_ui_thread(self):
        """Start the UI update thread."""
        if self.ui_thread is None or not self.ui_thread.is_alive():
            self.ui_running = True
            self.ui_thread = threading.Thread(target=self._ui_update_loop, daemon=True)
            self.ui_thread.start()
            if self.debug:
                self.logger.log_info("Started UI update thread")
    
    def stop_ui_thread(self):
        """Stop the UI update thread."""
        self.ui_running = False
        if self.ui_thread and self.ui_thread.is_alive():
            self.ui_thread.join(timeout=2)
            if self.debug:
                self.logger.log_info("Stopped UI update thread")
    
    def _ui_update_loop(self):
        """Main loop for UI updates in separate thread."""
        while self.ui_running:
            try:
                with self.ui_lock:
                    if self.current_chunk and self.progress_started and self.current_pbar:
                        self._update_progress_display()
                time.sleep(0.1)  # Update every 100ms for smooth animation
            except Exception as e:
                if self.debug:
                    self.logger.log_error(f"UI thread error: {e}")
    
    def _update_progress_display(self):
        """Update the progress display (called from UI thread)."""
        chunk_info = self.tracker.get_chunk_progress(self.current_chunk)
        if not chunk_info or not self.current_pbar:
            return
        
        # Update the progress bar
        self.current_pbar.n = chunk_info['completed_scenes']
        self.current_pbar.total = chunk_info['total_scenes']
        
        # Update the description with current scene info
        current_scene = self.tracker.get_current_scene_info()
        scene_name = ""
        if current_scene:
            scene_name = current_scene['movie_show'][:20] + "..." if len(current_scene['movie_show']) > 20 else current_scene['movie_show']
        
        avg_time = self.tracker.get_average_scene_time()
        avg_text = f" | Avg: {avg_time:.1f}s" if avg_time else ""
        
        # Update the postfix with elapsed time
        chunk = self.tracker.chunks.get(self.current_chunk)
        elapsed = ""
        if chunk and chunk.start_time:
            elapsed_seconds = (datetime.now() - chunk.start_time).total_seconds()
            elapsed = self._format_duration(elapsed_seconds)
        
        # Update the progress bar description and postfix
        # Note: tqdm handles colors automatically in the bar, description uses ANSI colors
        desc = f"🎯 {scene_name}{avg_text}"
        postfix = f"Elapsed: {elapsed}"
        
        self.current_pbar.set_description(desc)
        self.current_pbar.set_postfix_str(postfix)
        
        # Refresh the display
        self.current_pbar.refresh()
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _format_file_size(self, file_path: str) -> str:
        """Format file size in human readable format."""
        try:
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        except OSError:
            return "Unknown"
    
    def display_initial_summary(self, selected_chunks: Optional[List[int]] = None):
        """Display the initial processing summary."""
        if self.static_content_shown:
            return
            
        # Create header
        header = Panel.fit(
            "[bold blue]🎬 MARVEL MEGA CUT PROCESSOR v1.0[/bold blue]",
            border_style="blue"
        )
        self.console.print(header)
        
        # Processing summary
        progress = self.tracker.get_overall_progress()
        total_est_duration = sum(
            self.tracker.chunks[chunk_num].estimated_duration 
            for chunk_num in self.tracker.chunks.keys()
        )
        
        hours = int(total_est_duration // 3600)
        minutes = int((total_est_duration % 3600) // 60)
        duration_str = f"{hours}h {minutes}m"
        
        chunks_display = f" | Selected: {selected_chunks}" if selected_chunks else ""
        
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column(style="bold cyan")
        summary_table.add_column()
        
        summary_table.add_row("📋 PROCESSING SUMMARY", "")
        summary_table.add_row("   Total Scenes:", f"{progress['total_scenes']} | Valid: {progress['total_scenes']} | Invalid: 0")
        summary_table.add_row("   Chunks:", f"{progress['total_chunks']} total{chunks_display} | Est. Duration: {duration_str}")
        
        self.console.print(summary_table)
        self.console.print()  # Extra spacing
        
        self.static_content_shown = True
    
    def start_progress_display(self):
        """Start the progress display."""
        if not self.progress_started:
            self.progress_started = True
            self.start_ui_thread()
            print()  # Add a newline before progress starts
    
    def stop_progress_display(self):
        """Stop the progress display."""
        if self.progress_started:
            self.stop_ui_thread()
            if self.current_pbar:
                self.current_pbar.close()
            print()  # Add a newline after final progress
            self.progress_started = False
    
    def update_chunk_progress(self, chunk_number: int):
        """Update progress for a specific chunk with tqdm progress bar."""
        if not self.progress_started:
            self.start_progress_display()
        
        # Set the current chunk for the UI thread
        with self.ui_lock:
            self.current_chunk = chunk_number
            
            # Create or update the progress bar
            chunk_info = self.tracker.get_chunk_progress(chunk_number)
            if chunk_info and not self.current_pbar:
                # Create new progress bar for this chunk
                est_hours = int(chunk_info['estimated_duration'] // 3600)
                est_minutes = int((chunk_info['estimated_duration'] % 3600) // 60)
                desc = f"Chunk {chunk_number}/{len(self.tracker.chunks)} ({chunk_info['total_scenes']} scenes, ~{est_hours}h {est_minutes}m)"
                
                self.current_pbar = tqdm(
                    total=chunk_info['total_scenes'],
                    desc=desc,
                    unit="scenes",
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
                    leave=True,
                    colour='green'  # Add color to the progress bar
                )
    
    def update_scene_progress(self, scene_name: str, scene_num: int, total_scenes: int):
        """Update current scene processing progress."""
        # Scene progress is handled within chunk progress
        pass
    
    def complete_scene_progress(self):
        """Complete and hide the scene progress."""
        # Scene progress is handled within chunk progress
        pass
    
    def update_render_progress(self, message: str):
        """Show rendering progress."""
        if not self.progress_started:
            return
        
        # Print render progress on a new line
        print()  # New line after chunk progress
        render_line = f"🎬 Video Rendering: {message}"
        self.console.print(render_line)
    
    def complete_render_progress(self):
        """Complete and hide the render progress."""
        # Rendering completion is handled by chunk completion
        pass
    
    def display_complete_status(self):
        """Display final completion status."""
        self.stop_progress_display()
        
        progress = self.tracker.get_overall_progress()
        total_duration = self.tracker.get_processing_duration()
        
        # Print a clear completion message
        self.console.print("\n🎉 [bold green]PROCESSING COMPLETE![/bold green]")
        
        # Completion summary
        completion_panel = Panel(
            f"🎉 [bold green]PROCESSING COMPLETE![/bold green]\n"
            f"   ✅ Total scenes processed: {progress['completed_scenes']}\n" +
            (f"   ❌ Failed scenes: {progress['failed_scenes']}\n" if progress['failed_scenes'] > 0 else "") +
            f"   ⏱️  Total time: {total_duration}\n"
            f"   📄 Full logs: {self.logger.log_file}",
            border_style="green",
            title="Summary"
        )
        self.console.print(completion_panel)
        
        # Output files
        output_table = Table(title="📁 OUTPUT FILES", box=None)
        output_table.add_column("File", style="cyan")
        output_table.add_column("Size", style="green")
        
        for chunk_num, chunk in self.tracker.chunks.items():
            if chunk.output_file and chunk.status == "completed":
                file_size = self._format_file_size(chunk.output_file)
                filename = os.path.basename(chunk.output_file)
                output_table.add_row(f"• {filename}", file_size)
        
        if output_table.row_count > 0:
            self.console.print(output_table)
    
    def display_error_summary(self):
        """Display error summary if there were failures."""
        failed_scenes = [s for s in self.tracker.scenes if s.status == "failed"]
        if not failed_scenes:
            return
        
        # Group by error type
        error_groups = {}
        for scene in failed_scenes:
            error_type = scene.error_type.value if scene.error_type else "unknown"
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(scene.movie_show)
        
        error_table = Table(title=f"⚠️  ERROR SUMMARY ({len(failed_scenes)} failed scenes)", box=None)
        error_table.add_column("Error Type", style="red")
        error_table.add_column("Count", style="yellow")
        error_table.add_column("Examples", style="dim")
        
        for error_type, scene_names in error_groups.items():
            examples = ", ".join(scene_names[:2])
            if len(scene_names) > 2:
                examples += f", +{len(scene_names) - 2} more"
            
            error_table.add_row(
                error_type.replace('_', ' ').title(),
                str(len(scene_names)),
                examples
            )
        
        self.console.print(error_table)
        self.console.print(f"[dim]📄 Full error details in: {self.logger.log_file}[/dim]")
    
    def show_error(self, message: str):
        """Display a prominent error message."""
        print()  # New line before error
        error_panel = Panel(
            f"❌ [bold red]ERROR[/bold red]\n{message}",
            border_style="red",
            title="Error"
        )
        self.console.print(error_panel)
    
    def refresh_display(self):
        """Refresh the current display."""
        # tqdm handles refresh automatically
        pass 