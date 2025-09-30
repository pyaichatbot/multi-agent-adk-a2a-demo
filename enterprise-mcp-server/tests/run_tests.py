#!/usr/bin/env python3
"""
Simple Test Runner for SageAI MCP Server
Run all tests from the tests directory
"""

import asyncio
import sys
import os
from pathlib import Path

def main():
    """Main test runner function"""
    print("🧪 SageAI MCP Server Test Runner")
    print("=" * 50)
    
    # Add src to Python path
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path[0]}")
    
    # Import and run comprehensive tests
    try:
        from run_all_tests import ComprehensiveTestRunner
        
        async def run_tests():
            runner = ComprehensiveTestRunner()
            
            # Check for quick test flag
            if len(sys.argv) > 1 and sys.argv[1] == "--quick":
                print("💨 Running Quick Smoke Tests...")
                success = await runner.run_quick_smoke_tests()
                return success
            else:
                print("🚀 Running Comprehensive Test Suite...")
                await runner.run_all_test_suites()
                return True
        
        # Run tests
        success = asyncio.run(run_tests())
        
        if success:
            print("\n✅ Tests completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Tests failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Test runner failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()