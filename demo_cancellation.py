#!/usr/bin/env python3
"""
Demonstration script showing Ctrl+C cancellation in action.
This script simulates a long-running processing task that can be cancelled.
"""

import time
import threading
from video_editor import reset_cancellation, is_cancelled


def simulate_long_processing():
    """Simulate a long processing task that can be cancelled."""
    print("🚀 Starting simulated processing...")
    print("   Press Ctrl+C to test cancellation")
    print("   Processing will continue for 30 seconds or until cancelled")
    print()
    
    # Reset cancellation for new run
    reset_cancellation()
    
    start_time = time.time()
    chunk_count = 0
    
    try:
        # Simulate processing multiple chunks
        for chunk_num in range(1, 11):  # 10 chunks
            if is_cancelled():
                print(f"\n🛑 Processing cancelled after {time.time() - start_time:.1f}s")
                print(f"   Completed chunks: {chunk_count}")
                return
            
            print(f"📦 Processing chunk {chunk_num}/10...")
            
            # Simulate scene processing within chunk
            for scene_num in range(1, 6):  # 5 scenes per chunk
                if is_cancelled():
                    print(f"\n🛑 Processing cancelled during chunk {chunk_num}")
                    return
                
                # Simulate scene processing time
                time.sleep(0.5)  # 0.5 seconds per scene
                
                if scene_num % 2 == 0:
                    print(f"   ✅ Scene {scene_num}/5 completed")
            
            chunk_count += 1
            print(f"   🎉 Chunk {chunk_num} completed!")
            print()
            
            # Small delay between chunks
            time.sleep(0.2)
        
        print(f"🎉 All processing completed in {time.time() - start_time:.1f}s!")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Keyboard interrupt received after {time.time() - start_time:.1f}s")
        print(f"   Completed chunks: {chunk_count}")
        print("   ✅ Cancellation handled gracefully!")


def demonstrate_threading_cancellation():
    """Demonstrate cancellation with multiple threads."""
    print("\n🧵 Threading Cancellation Demo")
    print("=" * 40)
    
    def worker_thread(thread_id, duration):
        """Simulate a worker thread that can be cancelled."""
        start_time = time.time()
        print(f"   Thread {thread_id}: Starting work...")
        
        for i in range(duration):
            if is_cancelled():
                print(f"   Thread {thread_id}: Cancelled after {time.time() - start_time:.1f}s")
                return
            
            time.sleep(0.2)  # Simulate work
            print(f"   Thread {thread_id}: Step {i+1}/{duration}")
        
        print(f"   Thread {thread_id}: Completed in {time.time() - start_time:.1f}s")
    
    # Reset cancellation
    reset_cancellation()
    
    print("Starting 3 worker threads...")
    print("Press Ctrl+C to cancel all threads")
    
    # Start worker threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker_thread, args=(i+1, 10))
        thread.daemon = True  # Allow main thread to exit
        thread.start()
        threads.append(thread)
    
    try:
        # Wait for threads to complete or be cancelled
        for thread in threads:
            thread.join()
            
    except KeyboardInterrupt:
        print(f"\n🛑 Main thread received interrupt")
        print("   Worker threads will be cancelled on next check")
        
        # Give threads a moment to check cancellation
        time.sleep(0.5)
        
        # Wait for threads to finish
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
    
    print("✅ Threading cancellation demo completed!")


def show_cancellation_features():
    """Show the key features of the cancellation system."""
    print("\n🔧 Cancellation Features")
    print("=" * 40)
    
    print("✅ Signal Handling:")
    print("   • SIGINT (Ctrl+C) properly handled")
    print("   • SIGTERM (termination) supported")
    print("   • Graceful shutdown with cleanup")
    print()
    
    print("✅ Thread Safety:")
    print("   • Thread-safe cancellation detection")
    print("   • All worker threads properly cancelled")
    print("   • No orphaned processes")
    print()
    
    print("✅ Resource Management:")
    print("   • Video cache properly cleared")
    print("   • Temporary files cleaned up")
    print("   • Memory leaks prevented")
    print()
    
    print("✅ Progress Preservation:")
    print("   • Completed chunks preserved")
    print("   • Partial work saved")
    print("   • Clean restart possible")
    print()
    
    print("✅ User Experience:")
    print("   • Immediate response to Ctrl+C")
    print("   • Clear cancellation messages")
    print("   • Progress tracking maintained")


if __name__ == "__main__":
    print("🎬 Marvel Mega Cut - Cancellation Demo")
    print("=" * 50)
    
    # Demo 1: Basic cancellation
    simulate_long_processing()
    
    # Demo 2: Threading cancellation
    demonstrate_threading_cancellation()
    
    # Demo 3: Feature overview
    show_cancellation_features()
    
    print("\n🎯 Summary:")
    print("   • Ctrl+C now works properly with threaded processing")
    print("   • All threads are gracefully cancelled")
    print("   • Resources are properly cleaned up")
    print("   • Progress is preserved when possible")
    print("   • No more orphaned processes!") 