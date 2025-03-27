import React from 'react';
import { 
  AppBar,
  Toolbar,
  Typography,
  Box,
  Container,
  IconButton,
  useTheme
} from '@mui/material';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

// Note: Material UI v7 uses a different theme approach than Chakra UI
// Since we don't have a dark mode toggle in MUI setup yet, we'll just show the icon
// but it won't toggle themes until we set up a theme context

const Header: React.FC = () => {
  const theme = useTheme();
  // This would normally toggle between light and dark mode
  const handleToggleTheme = () => {
    console.log('Theme toggle clicked - functionality to be implemented');
  };

  return (
    <AppBar position="static" sx={{ boxShadow: 2 }}>
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <Box>
            <Typography variant="h5" component="h1">
              AI Benchmark Explorer
            </Typography>
            <Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>
              Explore benchmark datasets from Papers With Code
            </Typography>
          </Box>
          <Box sx={{ flexGrow: 1 }} />
          <IconButton
            color="inherit"
            onClick={handleToggleTheme}
            edge="end"
          >
            {theme.palette.mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
          </IconButton>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Header;
