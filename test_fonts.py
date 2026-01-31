#!/usr/bin/env python3

import moviepy
from moviepy.video.VideoClip import TextClip
import os
import platform

def test_available_fonts():
    """Test which fonts are available in MoviePy"""
    print("Testing available fonts in MoviePy...")
    print("=" * 50)
    
    # Try to list fonts if method exists
    try:
        available_fonts = TextClip.list('font')
        print(f"Available fonts ({len(available_fonts)}):")
        for font in available_fonts[:20]:  # Show first 20
            print(f"  - {font}")
        if len(available_fonts) > 20:
            print(f"  ... and {len(available_fonts) - 20} more")
    except Exception as e:
        print(f"Could not list fonts: {e}")
    
    print("\n" + "=" * 50)
    
    # Test common Windows fonts
    windows_fonts_to_test = [
        "Arial",
        "arial", 
        "Arial.ttf",
        "Calibri",
        "calibri",
        "Calibri.ttf", 
        "Times-New-Roman",
        "times-new-roman",
        "Verdana",
        "verdana",
        "Tahoma",
        "tahoma",
        "Comic-Sans-MS",
        "comic-sans-ms",
        "Georgia",
        "georgia",
        "Trebuchet-MS",
        "trebuchet-ms",
        None  # Default font
    ]
    
    print("Testing individual fonts:")
    working_fonts = []
    
    for font in windows_fonts_to_test:
        try:
            # Try to create a simple TextClip - use named parameters to avoid conflicts
            txt = TextClip(
                text="Test", 
                font_size=20, 
                color='white', 
                font=font, 
                duration=1
            )
            txt.close()  # Clean up
            print(f"✓ {font if font else 'Default font'} - WORKS")
            working_fonts.append(font)
        except Exception as e:
            print(f"✗ {font if font else 'Default font'} - FAILED: {e}")
    
    print(f"\nWorking fonts: {working_fonts}")
    return working_fonts

if __name__ == "__main__":
    print(f"Platform: {platform.system()}")
    print(f"Python MoviePy version: {moviepy.__version__}")
    working_fonts = test_available_fonts()
    
    if working_fonts:
        print(f"\n✓ Found {len(working_fonts)} working fonts!")
        print("You can use these fonts in your video editor.")
    else:
        print("\n✗ No working fonts found!")
        print("This means there might be a font system issue.") 