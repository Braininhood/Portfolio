import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Badge,
  Chip,
  useTheme,
  useMediaQuery,
  Divider,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Devices as DevicesIcon,
  Security as SecurityIcon,
  Timeline as TimelineIcon,
  NetworkCheck as NetworkTrafficIcon,
  Help as HelpIcon,
  Close as CloseIcon,
  Circle as CircleIcon,
  Psychology as AIIcon,
} from '@mui/icons-material';
import useRealTimeDevices from '../../hooks/useRealTimeDevices';

const drawerWidth = 280;

const Layout = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const {
    devices,
    networkStats,
    connectionInfo,
    onlineDevices,
    offlineDevices,
    notifications
  } = useRealTimeDevices();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const menuItems = [
    {
      text: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/',
      badge: null,
    },
    {
      text: 'Network Devices',
      icon: <DevicesIcon />,
      path: '/devices',
      badge: devices.length > 0 ? devices.length : null,
    },
    {
      text: 'Network Scans',
      icon: <TimelineIcon />,
      path: '/scans',
      badge: null,
    },
    {
      text: 'Network Traffic',
      icon: <NetworkTrafficIcon />,
      path: '/traffic',
      badge: null,
    },
    {
      text: 'Security Events',
      icon: <SecurityIcon />,
      path: '/security-events',
      badge: networkStats.unresolved_alerts > 0 ? networkStats.unresolved_alerts : null,
    },
    {
      text: 'AI Dashboard',
      icon: <AIIcon />,
      path: '/ai-dashboard',
      badge: null,
    },
    {
      text: 'Help',
      icon: <HelpIcon />,
      path: '/settings',
      badge: null,
    },
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected':
        return 'success';
      case 'polling':
        return 'success';
      case 'connecting':
      case 'reconnecting':
      case 'loading':
      case 'initializing':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'connected':
        return <CircleIcon sx={{ fontSize: 12, color: '#4caf50' }} />;
      case 'polling':
        return <CircleIcon sx={{ fontSize: 12, color: '#2196f3' }} />;
      case 'connecting':
      case 'reconnecting':
      case 'loading':
      case 'initializing':
        return <CircleIcon sx={{ fontSize: 12, color: '#ff9800' }} />;
      case 'error':
        return <CircleIcon sx={{ fontSize: 12, color: '#f44336' }} />;
      default:
        return <CircleIcon sx={{ fontSize: 12, color: '#9e9e9e' }} />;
    }
  };

  const drawer = (
    <Box sx={{ height: '100%', bgcolor: 'background.paper' }}>
      {/* Header */}
      <Box
        sx={{
          p: 2,
          background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
          color: 'white',
        }}
      >
        <Typography variant="h6" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
          Network Security Monitor
        </Typography>
        
        {/* Connection Status */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {getStatusIcon(connectionInfo.status)}
          <Typography variant="caption" sx={{ opacity: 0.9 }}>
            {connectionInfo.text}
          </Typography>
        </Box>
      </Box>

      <Divider />

      {/* Live Stats */}
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Live Statistics
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          <Chip
            size="small"
            icon={<CircleIcon sx={{ fontSize: 12, color: '#4caf50' }} />}
            label={`${onlineDevices.length} Online`}
            variant="outlined"
            color="success"
          />
          <Chip
            size="small"
            icon={<CircleIcon sx={{ fontSize: 12, color: '#f44336' }} />}
            label={`${offlineDevices.length} Offline`}
            variant="outlined"
            color="error"
          />
          {networkStats.unresolved_alerts > 0 && (
            <Chip
              size="small"
              label={`${networkStats.unresolved_alerts} Alerts`}
              color="warning"
              variant="filled"
            />
          )}
        </Box>
        
        {networkStats.last_updated && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Last updated: {new Date(networkStats.last_updated).toLocaleTimeString()}
          </Typography>
        )}
      </Box>

      <Divider />

      {/* Navigation */}
      <List sx={{ flexGrow: 1, py: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                if (isMobile) {
                  setMobileOpen(false);
                }
              }}
              sx={{
                mx: 1,
                borderRadius: 1,
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: 'primary.contrastText',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                  },
                  '& .MuiListItemIcon-root': {
                    color: 'primary.contrastText',
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: location.pathname === item.path ? 'inherit' : 'action.active',
                }}
              >
                {item.badge ? (
                  <Badge badgeContent={item.badge} color="error" max={99}>
                    {item.icon}
                  </Badge>
                ) : (
                  item.icon
                )}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.875rem',
                  fontWeight: location.pathname === item.path ? 'bold' : 'normal',
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {/* Notifications */}
      {notifications.length > 0 && (
        <>
          <Divider />
          <Box sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Recent Notifications
            </Typography>
            <Box sx={{ maxHeight: 120, overflow: 'auto' }}>
              {notifications.slice(-3).map((notification) => (
                <Box
                  key={notification.id}
                  sx={{
                    p: 1,
                    mb: 1,
                    bgcolor: notification.type === 'error' ? 'error.light' : 
                            notification.type === 'success' ? 'success.light' : 
                            notification.type === 'warning' ? 'warning.light' : 'info.light',
                    borderRadius: 1,
                    opacity: 0.8,
                  }}
                >
                  <Typography variant="caption" color="text.primary">
                    {notification.message}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
        </>
      )}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <CssBaseline />
      
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          bgcolor: 'background.paper',
          color: 'text.primary',
          boxShadow: 1,
        }}
      >
        <Toolbar>
          <IconButton
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Network Security Monitor
          </Typography>
          
          {/* Status Chip in App Bar */}
          <Chip
            icon={getStatusIcon(connectionInfo.status)}
            label={connectionInfo.text}
            size="small"
            color={getStatusColor(connectionInfo.status)}
            variant="outlined"
          />
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
        >
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', p: 1 }}>
            <IconButton onClick={handleDrawerToggle}>
              <CloseIcon />
            </IconButton>
          </Box>
          {drawer}
        </Drawer>

        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: 8, // Account for AppBar height
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default Layout; 