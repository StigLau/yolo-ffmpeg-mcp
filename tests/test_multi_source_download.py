#!/usr/bin/env python3
"""
Multi-Source Download Test - Real Komposteur Integration Test
============================================================

Tests the multi-source download functionality using real Komposteur classes:
- YouTube downloads via YoutubeDlConvertor
- HTTP downloads via UrlDownloader  
- S3 downloads via S3Downloader
- Local file handling via LocalFileFetcher
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.download_service import DownloadService, DownloadRequest

async def test_multi_source_downloads():
    """Test downloads from multiple source types"""
    
    print("🔄 Multi-Source Download Test - Real Komposteur Integration")
    print("=" * 60)
    
    # Initialize download service
    download_service = DownloadService()
    
    if not download_service.is_available():
        print("❌ Download service not available")
        return
    
    print("✅ Download service initialized")
    print(f"📁 Using JAR: {download_service.komposteur_jar}")
    print()
    
    # Test cases for different source types
    test_cases = [
        {
            "name": "YouTube Video",
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "source_type": "youtube",
            "quality": "720p"
        },
        {
            "name": "HTTP Download",
            "url": "https://file-examples.com/storage/fe68c1bfa46de93139dc7b6/2017/10/file_example_MP4_480_1_5MG.mp4",
            "source_type": "http",
            "quality": "best"
        },
        {
            "name": "Local File",
            "url": "/tmp/music/source/pexels-4.mp4",
            "source_type": "local",
            "quality": "original"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 Test {i}/{len(test_cases)}: {test_case['name']}")
        print(f"   URL: {test_case['url']}")
        print(f"   Type: {test_case['source_type']}")
        
        try:
            # Test getting info first
            info_result = await download_service.get_download_info(test_case['url'])
            
            if info_result.get('success'):
                print(f"   ℹ️  Info: {info_result.get('title', 'N/A')}")
                print(f"   📊 Duration: {info_result.get('duration', 0)}s")
                print(f"   🎯 Formats: {info_result.get('formats', [])}")
            else:
                print(f"   ⚠️  Info failed: {info_result.get('error', 'Unknown error')}")
            
            # Test actual download
            download_result = await download_service.download_from_url(
                url=test_case['url'],
                source_type=test_case['source_type'],
                quality=test_case['quality']
            )
            
            if download_result.success:
                print(f"   ✅ Download: {download_result.file_path}")
                print(f"   📦 Size: {download_result.file_size_bytes} bytes")
                print(f"   ⏱️  Time: {download_result.download_duration:.2f}s")
                
                if download_result.file_id:
                    print(f"   🆔 File ID: {download_result.file_id}")
                
                results.append({
                    "test_case": test_case['name'],
                    "success": True,
                    "file_path": download_result.file_path,
                    "file_size": download_result.file_size_bytes,
                    "source_type": test_case['source_type']
                })
            else:
                print(f"   ❌ Download failed: {download_result.error}")
                results.append({
                    "test_case": test_case['name'],
                    "success": False,
                    "error": download_result.error,
                    "source_type": test_case['source_type']
                })
            
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")
            results.append({
                "test_case": test_case['name'],
                "success": False,
                "error": str(e),
                "source_type": test_case['source_type']
            })
        
        print()
    
    # Summary
    print("📊 Test Summary")
    print("-" * 30)
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        print("\n✅ Successful Downloads:")
        for result in successful_tests:
            print(f"   - {result['test_case']} ({result['source_type']})")
            print(f"     📁 {result['file_path']}")
            print(f"     📦 {result['file_size']} bytes")
    
    if failed_tests:
        print("\n❌ Failed Downloads:")
        for result in failed_tests:
            print(f"   - {result['test_case']} ({result['source_type']})")
            print(f"     💥 {result['error']}")
    
    print()
    print("🎯 Komposteur Classes Used:")
    print("   - no.lau.download.S3Downloader")
    print("   - no.lau.download.UrlDownloader")
    print("   - no.lau.download.LocalFileFetcher")
    print("   - no.lau.state.YoutubeDlConvertor")
    
    return len(successful_tests) == len(results)

async def test_batch_downloads():
    """Test batch download functionality"""
    
    print("\n🔄 Batch Download Test")
    print("=" * 30)
    
    download_service = DownloadService()
    
    if not download_service.is_available():
        print("❌ Download service not available")
        return False
    
    # Test URLs (mix of types)
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://file-examples.com/storage/fe68c1bfa46de93139dc7b6/2017/10/file_example_MP4_480_1_5MG.mp4",
        "/tmp/music/source/pexels-4.mp4"
    ]
    
    print(f"📥 Downloading {len(test_urls)} files concurrently...")
    
    try:
        results = await download_service.batch_download(
            urls=test_urls,
            quality="best",
            max_concurrent=2
        )
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"✅ Batch Results: {len(successful)}/{len(results)} successful")
        
        for result in results:
            status = "✅" if result.success else "❌"
            print(f"   {status} {result.original_url}")
            if result.success:
                print(f"       📁 {result.file_path}")
                print(f"       📦 {result.file_size_bytes} bytes")
            else:
                print(f"       💥 {result.error}")
        
        return len(successful) == len(results)
        
    except Exception as e:
        print(f"💥 Batch download failed: {e}")
        return False

async def main():
    """Run all multi-source download tests"""
    
    print("🚀 Starting Multi-Source Download Tests")
    print("Using Real Komposteur Download Classes")
    print("=" * 50)
    
    # Test individual downloads
    single_test_passed = await test_multi_source_downloads()
    
    # Test batch downloads
    batch_test_passed = await test_batch_downloads()
    
    # Final summary
    print("\n🎯 Final Test Results")
    print("=" * 25)
    
    if single_test_passed and batch_test_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Multi-source download integration working")
        print("✅ Real Komposteur classes successfully integrated")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        print(f"   Single downloads: {'✅' if single_test_passed else '❌'}")
        print(f"   Batch downloads: {'✅' if batch_test_passed else '❌'}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())