# MacBook Disk Monitoring & JIRA Ticketing System

A comprehensive, open-source disk monitoring solution for macOS that automatically creates JIRA tickets when disk health issues are detected.

## Overview

This system monitors disk space usage and SMART health metrics using Prometheus, Node Exporter, and smartmontools. When critical thresholds are exceeded, it automatically creates JIRA tickets assigned to the Datacenter Operations team.

## Features

- **Disk Space Monitoring**: Tracks usage on all mounted filesystems
- **SMART Health Monitoring**: Monitors disk health using smartmontools
- **Automated Alerting**: Configurable thresholds for warnings and critical alerts
- **JIRA Integration**: Automatic ticket creation with detailed alert information
- **Local Operation**: Runs entirely on your MacBook without external dependencies
- **Open Source**: Uses only free and open-source tools

## Architecture

