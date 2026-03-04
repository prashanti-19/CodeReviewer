import { createBrowserRouter } from 'react-router';
import { Upload } from './pages/Upload';
import { Processing } from './pages/Processing';
import { Results } from './pages/Results';

export const router = createBrowserRouter([
  {
    path: '/',
    Component: Upload,
  },
  {
    path: '/processing/:jobId',
    Component: Processing,
  },
  {
    path: '/results/:jobId',
    Component: Results,
  },
]);
