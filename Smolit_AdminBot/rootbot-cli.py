#!/usr/bin/env python3

import os
import sys
import click
import psutil
import logging
from typing import Dict, Any
from root_bot.logger_config import setup_logging
from root_bot.security_manager import SecurityManager
from root_bot.resource_monitor import ResourceMonitor
from root_bot.process_monitor import ProcessMonitor

setup_logging()
logger = logging.getLogger('RootBot.cli')

@click.group()
def cli():
    """RootBot CLI - Advanced management interface"""
    pass

@cli.command()
def scan():
    """Perform a security scan of the system"""
    try:
        security = SecurityManager({
            'config': '/etc/rootbot/config.py',
            'memory': '/var/lib/rootbot/memory.json',
            'service': '/etc/systemd/system/rootbot.service'
        })
        
        results = {}
        for file_type in ['config', 'memory', 'service']:
            results[file_type] = security.verify_file_integrity(file_type)
            
        click.echo(f"Security scan results:")
        for file_type, is_valid in results.items():
            status = click.style("✓", fg="green") if is_valid else click.style("✗", fg="red")
            click.echo(f"{status} {file_type}: {'Valid' if is_valid else 'Invalid'}")
            
    except Exception as e:
        logger.error(f"Security scan failed: {str(e)}")
        click.echo(click.style(f"Error: {str(e)}", fg="red"))
        sys.exit(1)

@cli.command()
def status():
    """Check the status of monitored services and resources"""
    try:
        # Check process status
        process_monitor = ProcessMonitor()
        pid = process_monitor.read_pid()
        is_running = process_monitor.is_process_running(pid) if pid else False
        
        # Check resource usage
        resource_monitor = ResourceMonitor()
        metrics = resource_monitor.check_resources()
        
        # Display status
        click.echo("\nRootBot Status:")
        status = click.style("RUNNING", fg="green") if is_running else click.style("STOPPED", fg="red")
        click.echo(f"Process: {status} (PID: {pid if pid else 'N/A'})")
        
        click.echo("\nResource Usage:")
        click.echo(f"CPU: {metrics['cpu']['percent']}%")
        click.echo(f"Memory: {metrics['memory']['percent']}%")
        click.echo(f"Disk: {metrics['disk']['percent']}%")
        
        if 'alerts' in metrics:
            click.echo("\nAlerts:")
            for resource, alert in metrics['alerts'].items():
                click.echo(click.style(
                    f"⚠ {resource.upper()}: {alert['current']}% (threshold: {alert['threshold']}%)",
                    fg="yellow"
                ))
                
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        click.echo(click.style(f"Error: {str(e)}", fg="red"))
        sys.exit(1)

@cli.command()
@click.argument('component')
def restart(component):
    """Restart a specific component (bot/watchdog)"""
    try:
        if component not in ['bot', 'watchdog']:
            raise ValueError(f"Invalid component: {component}")
            
        pid_file = f"/var/run/rootbot{'_watchdog' if component == 'watchdog' else ''}.pid"
        
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
                
            process = psutil.Process(pid)
            click.echo(f"Stopping {component}...")
            process.terminate()
            
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                click.echo("Force killing process...")
                process.kill()
                
            os.remove(pid_file)
            
        # Start the component
        if component == 'bot':
            os.system('systemctl start rootbot')
        else:
            os.system('python3 watchdog.py &')
            
        click.echo(click.style(f"{component.capitalize()} restarted successfully", fg="green"))
        
    except Exception as e:
        logger.error(f"Restart failed: {str(e)}")
        click.echo(click.style(f"Error: {str(e)}", fg="red"))
        sys.exit(1)

if __name__ == '__main__':
    cli()
