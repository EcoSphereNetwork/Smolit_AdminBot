# RootBot Troubleshooting Guide

## Common Installation Issues

### Permission Errors
```
Error: Permission denied when accessing /var/log/rootbot
```
**Solution:**
1. Verify user permissions:
```bash
sudo ls -l /var/log/rootbot
```
2. Fix permissions:
```bash
sudo chown -R root_adminbot:adminbot_group /var/log/rootbot
sudo chmod 750 /var/log/rootbot
```

### LlamaFile Server Issues
```
Error: Failed to start LLM server
```
**Solution:**
1. Check if LlamaFile is properly installed:
```bash
ls -l /usr/local/bin/llamafile
```
2. Verify model file exists:
```bash
ls -l /path/to/model.bin
```
3. Check server logs:
```bash
tail -f /var/log/rootbot/llm_server.log
```

### Resource Limit Issues
```
Error: Process exceeded resource limits
```
**Solution:**
1. Check current resource usage:
```bash
top -u root_adminbot
```
2. Adjust limits in config:
```python
RESOURCE_LIMITS = {
    'max_cpu_per_process': 50,  # Decrease if needed
    'max_memory_per_process': 25  # Decrease if needed
}
```

## Runtime Issues

### High CPU Usage
**Symptoms:**
- System slowdown
- High load average
- Frequent CPU threshold alerts

**Solutions:**
1. Check process priorities:
```bash
ps -eo pid,ppid,cmd,%cpu,%mem --sort=-%cpu | head
```
2. Adjust monitoring interval:
```python
MONITORING_INTERVAL = 120  # Increase to reduce overhead
```
3. Reduce LLM thread count:
```python
LLAMAFILE_SETTINGS = {
    'threads': 2  # Decrease thread count
}
```

### Memory Leaks
**Symptoms:**
- Increasing memory usage over time
- Slow response times
- OOM killer activation

**Solutions:**
1. Check memory usage:
```bash
ps -o pid,ppid,rss,cmd ax | grep root_adminbot
```
2. Enable memory compaction:
```python
MEMORY_COMPACTION_THRESHOLD = 1000
```
3. Reduce memory limits:
```python
SHORT_TERM_MEMORY_SIZE = 500
```

### Network Issues
**Symptoms:**
- Connection timeouts
- High latency
- Network-related errors

**Solutions:**
1. Check network connections:
```bash
netstat -tuln | grep root_adminbot
```
2. Verify firewall rules:
```bash
sudo iptables -L | grep root_adminbot
```
3. Check DNS resolution:
```bash
nslookup example.com
```

## Log Analysis

### Error Severity Levels
- **CRITICAL**: Immediate attention required
- **ERROR**: System functionality affected
- **WARNING**: Potential issues detected
- **INFO**: Normal operation events
- **DEBUG**: Detailed debugging information

### Common Error Messages

1. **Configuration Errors**
```
ERROR: Invalid configuration parameter
```
- Check config.py for syntax errors
- Verify all required parameters are set
- Validate parameter types and ranges

2. **Resource Errors**
```
WARNING: Resource threshold exceeded
```
- Monitor system resources
- Adjust thresholds if needed
- Check for resource-intensive processes

3. **Security Errors**
```
ERROR: Command execution blocked
```
- Review allowed commands list
- Check user permissions
- Verify security policies

## Performance Optimization

### System Tuning
1. Adjust process nice values:
```bash
sudo renice -n 10 -p $(pgrep root_adminbot)
```

2. Set I/O priorities:
```bash
sudo ionice -c 2 -n 7 -p $(pgrep root_adminbot)
```

3. Configure memory limits:
```bash
sudo systemctl set-property root_adminbot MemoryLimit=512M
```

### Database Optimization
1. Enable memory compaction:
```python
MEMORY_COMPACTION_ENABLED = True
MEMORY_COMPACTION_INTERVAL = 3600
```

2. Optimize query patterns:
```python
QUERY_CACHE_SIZE = 1000
QUERY_TIMEOUT = 30
```

## Recovery Procedures

### Emergency Shutdown
```bash
./stop_bot.sh --force
```

### Data Recovery
1. Backup restoration:
```bash
./restore_backup.sh --latest
```

2. Memory state recovery:
```bash
./recover_memory.sh --verify
```

### System Reset
```bash
./reset_bot.sh --keep-config
```

## Getting Help

### Log Collection
```bash
./collect_logs.sh --last-24h
```

### System Information
```bash
./system_info.sh --full
```

### Support Channels
- GitHub Issues: [Report Issues](https://github.com/EcoSphereNetwork/Smolit_AdminBot/issues)
- Documentation: [Online Docs](https://github.com/EcoSphereNetwork/Smolit_AdminBot/docs)
- Community: [Discussion Forum](https://github.com/EcoSphereNetwork/Smolit_AdminBot/discussions)
