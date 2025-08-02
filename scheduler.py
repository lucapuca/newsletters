"""
Scheduler Script

Runs the newsletter digest pipeline on a schedule.
Can be used with cron or run continuously.
"""

import os
import time
import schedule
import logging
from datetime import datetime
from dotenv import load_dotenv

from main import NewsletterDigestPipeline

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class NewsletterScheduler:
    """Scheduler for running the newsletter digest pipeline."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.pipeline = None
        self.is_running = False
        
    def initialize_pipeline(self):
        """Initialize the newsletter digest pipeline."""
        try:
            self.pipeline = NewsletterDigestPipeline()
            logger.info("Pipeline initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            return False
    
    def run_digest(self):
        """Run the newsletter digest pipeline."""
        if not self.pipeline:
            if not self.initialize_pipeline():
                logger.error("Cannot run digest - pipeline not initialized")
                return
        
        try:
            logger.info("Starting scheduled newsletter digest")
            start_time = datetime.now()
            
            # Run the pipeline
            results = self.pipeline.run()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if results['success']:
                logger.info(f"Digest completed successfully in {duration:.2f} seconds")
                logger.info(f"Processed {results.get('processed_newsletters', 0)} newsletters")
                logger.info(f"Created {results.get('notion_results', {}).get('success_count', 0)} Notion entries")
            else:
                logger.error(f"Digest failed: {results.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error running digest: {e}")
    
    def run_daily_at(self, time_str: str):
        """
        Schedule the digest to run daily at a specific time.
        
        Args:
            time_str: Time in HH:MM format (e.g., "09:00")
        """
        schedule.every().day.at(time_str).do(self.run_digest)
        logger.info(f"Scheduled daily digest at {time_str}")
    
    def run_weekly_on(self, day: str, time_str: str):
        """
        Schedule the digest to run weekly on a specific day and time.
        
        Args:
            day: Day of the week (monday, tuesday, etc.)
            time_str: Time in HH:MM format
        """
        getattr(schedule.every(), day).at(time_str).do(self.run_digest)
        logger.info(f"Scheduled weekly digest on {day} at {time_str}")
    
    def run_every_hours(self, hours: int):
        """
        Schedule the digest to run every N hours.
        
        Args:
            hours: Number of hours between runs
        """
        schedule.every(hours).hours.do(self.run_digest)
        logger.info(f"Scheduled digest every {hours} hours")
    
    def run_immediately(self):
        """Run the digest immediately."""
        logger.info("Running digest immediately")
        self.run_digest()
    
    def start_scheduler(self, run_immediately: bool = False):
        """
        Start the scheduler loop.
        
        Args:
            run_immediately: Whether to run the digest immediately on startup
        """
        if run_immediately:
            self.run_immediately()
        
        logger.info("Starting scheduler...")
        logger.info("Press Ctrl+C to stop")
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            self.is_running = False
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            self.is_running = False
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        self.is_running = False
        logger.info("Scheduler stopped")
    
    def get_schedule_info(self):
        """Get information about the current schedule."""
        jobs = schedule.get_jobs()
        if jobs:
            logger.info(f"Current schedule: {len(jobs)} job(s)")
            for i, job in enumerate(jobs):
                logger.info(f"Job {i+1}: {job}")
        else:
            logger.info("No jobs scheduled")

def main():
    """Main entry point for the scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Newsletter Digest Scheduler')
    parser.add_argument('--daily', type=str, help='Run daily at time (HH:MM)')
    parser.add_argument('--weekly', type=str, help='Run weekly on day at time (day HH:MM)')
    parser.add_argument('--hours', type=int, help='Run every N hours')
    parser.add_argument('--now', action='store_true', help='Run immediately')
    parser.add_argument('--info', action='store_true', help='Show schedule info')
    
    args = parser.parse_args()
    
    scheduler = NewsletterScheduler()
    
    # Initialize pipeline
    if not scheduler.initialize_pipeline():
        logger.error("Failed to initialize pipeline. Exiting.")
        return
    
    # Set up schedule based on arguments
    if args.daily:
        scheduler.run_daily_at(args.daily)
    elif args.weekly:
        try:
            day, time_str = args.weekly.split()
            scheduler.run_weekly_on(day.lower(), time_str)
        except ValueError:
            logger.error("Weekly schedule format: day HH:MM (e.g., 'monday 09:00')")
            return
    elif args.hours:
        scheduler.run_every_hours(args.hours)
    else:
        # Default: run daily at 9 AM
        scheduler.run_daily_at("09:00")
        logger.info("No schedule specified, defaulting to daily at 09:00")
    
    # Show schedule info
    scheduler.get_schedule_info()
    
    # Start scheduler
    scheduler.start_scheduler(run_immediately=args.now)

if __name__ == "__main__":
    main() 