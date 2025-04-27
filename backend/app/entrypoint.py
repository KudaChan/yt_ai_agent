import os
import sys
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def start_api():
    """Start the FastAPI server"""
    logger.info("Starting API server...")
    subprocess.run(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])

def start_agents():
    """Start the Kafka consumer agents"""
    logger.info("Starting agents...")
    subprocess.run(["python", "-m", "app.run_agents"])

def start_all():
    """Start both API and agents in separate processes"""
    import multiprocessing
    
    api_process = multiprocessing.Process(target=start_api)
    agents_process = multiprocessing.Process(target=start_agents)
    
    api_process.start()
    agents_process.start()
    
    api_process.join()
    agents_process.join()

if __name__ == "__main__":
    service_type = os.environ.get("SERVICE_TYPE", "all").lower()
    
    if service_type == "api":
        start_api()
    elif service_type == "agents":
        start_agents()
    elif service_type == "all":
        start_all()
    else:
        logger.error(f"Unknown service type: {service_type}")
        sys.exit(1)