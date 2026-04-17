#!/usr/bin/env python
"""
DiamondVault Auction Automation Starter
This script starts the automated auction management system
"""

import subprocess
import sys
import os
import time

def main():
    print("🚀 DiamondVault Auction Automation System")
    print("=" * 50)
    print("This system will automatically:")
    print("1. Check for ended auctions every 60 seconds")
    print("2. Declare winners for ended auctions")
    print("3. Update auction statuses")
    print("4. Handle overdue payments")
    print("=" * 50)
    print("Press Ctrl+C to stop at any time")
    print()
    
    try:
        # Change to project directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Run the scheduler
        subprocess.run([sys.executable, 'manage.py', 'scheduler', '--interval', '60'])
        
    except KeyboardInterrupt:
        print("\n✅ Automation stopped by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    main()
