import asyncio
import sys
import os
from typing import List, Tuple
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from dotenv import load_dotenv

from core.config import settings
from core.mistral_service import mistral_service

load_dotenv()

class StartupHealthChecker:
    """Comprehensive health checker for all system components"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def log_error(self, component: str, message: str):
        """Log an error that prevents startup"""
        error_msg = f"ERROR {component}: {message}"
        self.errors.append(error_msg)
        print(error_msg)
        
    def log_warning(self, component: str, message: str):
        """Log a warning that doesn't prevent startup"""
        warning_msg = f"WARNING {component}: {message}"
        self.warnings.append(warning_msg)
        print(warning_msg)
        
    def log_success(self, component: str, message: str):
        """Log a successful check"""
        success_msg = f"SUCCESS {component}: {message}"
        print(success_msg)
    
    async def check_environment_variables(self) -> bool:
        """Check if all required environment variables are set"""
        print("\nChecking Environment Variables...")
        
        required_vars = [
            ("MONGODB_URL", "Database connection string"),
            ("DATABASE_NAME", "Database name"),
            ("DATABASE_TYPE", "Database type"),
            ("MISTRAL_API_KEY", "Mistral AI API key"),
            ("MISTRAL_API_ENDPOINT", "Mistral AI endpoint"),
            ("MISTRAL_MODEL", "Mistral AI model")
        ]
        
        all_good = True
        
        for var_name, description in required_vars:
            value = os.getenv(var_name)
            if not value:
                self.log_error("Environment", f"Missing {var_name} ({description})")
                all_good = False
            elif var_name == "MISTRAL_API_KEY" and len(value) < 10:
                self.log_error("Environment", f"Invalid {var_name} - too short")
                all_good = False
            else:
                self.log_success("Environment", f"{var_name} is configured")
        
        return all_good
    
    async def check_database_connection(self) -> bool:
        """Check MongoDB database connection"""
        print("\nChecking Database Connection...")
        
        try:
            client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
            
            await client.admin.command('ping')
            
            db = client[settings.DATABASE_NAME]
            collections = await db.list_collection_names()
            
            client.close()
            
            self.log_success("Database", f"Connected to MongoDB at {settings.MONGODB_URL}")
            self.log_success("Database", f"Database '{settings.DATABASE_NAME}' is accessible")
            
            if not collections:
                self.log_warning("Database", "Database is empty - will be initialized on first use")
            else:
                self.log_success("Database", f"Found {len(collections)} collections")
            
            return True
            
        except Exception as e:
            self.log_error("Database", f"Cannot connect to MongoDB: {str(e)}")
            self.log_error("Database", "Please ensure MongoDB is running and accessible")
            return False
    
    async def check_mistral_ai_service(self) -> bool:
        """Check Mistral AI service connectivity and authentication"""
        print("\nChecking Mistral AI Service...")
        
        try:
            if not settings.MISTRAL_API_KEY:
                self.log_error("Mistral AI", "API key is not configured")
                return False
            
            if len(settings.MISTRAL_API_KEY) < 20:
                self.log_error("Mistral AI", "API key appears to be invalid (too short)")
                return False
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.MISTRAL_API_KEY}"
            }
            
            payload = {
                "model": settings.MISTRAL_MODEL,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 10
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    settings.MISTRAL_API_ENDPOINT,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    self.log_success("Mistral AI", f"API is accessible with model {settings.MISTRAL_MODEL}")
                    self.log_success("Mistral AI", "Authentication successful")
                    return True
                elif response.status_code == 401:
                    self.log_error("Mistral AI", "Authentication failed - invalid API key")
                    return False
                elif response.status_code == 429:
                    self.log_warning("Mistral AI", "API rate limit reached - but connection is working")
                    return True
                else:
                    self.log_error("Mistral AI", f"API returned status code {response.status_code}")
                    return False
                    
        except httpx.TimeoutException:
            self.log_error("Mistral AI", "API request timed out - check internet connection")
            return False
        except httpx.RequestError as e:
            self.log_error("Mistral AI", f"Network error: {str(e)}")
            return False
        except Exception as e:
            self.log_error("Mistral AI", f"Unexpected error: {str(e)}")
            return False
    
    async def check_server_configuration(self) -> bool:
        """Check server configuration"""
        print("\nChecking Server Configuration...")
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((settings.HOST, settings.PORT))
            sock.close()
            
            if result == 0:
                self.log_error("Server", f"Port {settings.PORT} is already in use")
                self.log_error("Server", "Cannot start server - port is occupied by another process")
                return False
            else:
                self.log_success("Server", f"Port {settings.PORT} is available")
            
            if settings.HOST in ["127.0.0.1", "localhost"]:
                self.log_success("Server", f"Server will run on {settings.HOST}:{settings.PORT}")
            else:
                self.log_warning("Server", f"Server configured for external access on {settings.HOST}")
            
            return True
            
        except Exception as e:
            self.log_warning("Server", f"Cannot check port availability: {str(e)}")
            return True
    
    async def check_file_permissions(self) -> bool:
        """Check if we can write to necessary directories"""
        print("\nChecking File Permissions...")
        
        try:
            test_file = "test_write_permission.tmp"
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            
            self.log_success("Permissions", "Write access to current directory is available")
            return True
            
        except Exception as e:
            self.log_error("Permissions", f"Cannot write to current directory: {str(e)}")
            return False
    
    async def run_all_checks(self) -> bool:
        """Run all health checks"""
        print("Starting Pre-Flight Health Checks...")
        print("=" * 60)
        
        checks = [
            ("Environment Variables", self.check_environment_variables()),
            ("File Permissions", self.check_file_permissions()),
            ("Database Connection", self.check_database_connection()),
            ("Mistral AI Service", self.check_mistral_ai_service()),
            ("Server Configuration", self.check_server_configuration())
        ]
        
        results = []
        for check_name, check_coroutine in checks:
            try:
                result = await check_coroutine
                results.append(result)
            except Exception as e:
                self.log_error(check_name, f"Health check failed with exception: {str(e)}")
                results.append(False)
        
        print("\n" + "=" * 60)
        print("Health Check Summary:")
        
        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for error in self.errors:
                print(f"   {error}")
            print("\nCannot start server due to the above errors!")
            return False
        
        all_passed = all(results)
        if all_passed:
            print("\nAll health checks passed! Starting server...")
        
        return all_passed

async def run_startup_checks() -> bool:
    """Main function to run all startup checks"""
    checker = StartupHealthChecker()
    return await checker.run_all_checks()

def startup_check_sync() -> bool:
    """Synchronous wrapper for startup checks"""
    return asyncio.run(run_startup_checks())

if __name__ == "__main__":
    success = startup_check_sync()
    sys.exit(0 if success else 1)
