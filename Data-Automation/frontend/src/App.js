import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import FileUpload from './pages/FileUpload';
import DataAnalysis from './pages/DataAnalysis';
import CohortManagement from './pages/CohortManagement';
import EmailSystem from './pages/EmailSystem';
import Reports from './pages/Reports';
import BPADemo from './pages/BPADemo';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<FileUpload />} />
              <Route path="/analysis" element={<DataAnalysis />} />
              <Route path="/cohorts" element={<CohortManagement />} />
              <Route path="/email" element={<EmailSystem />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/bpa-demo" element={<BPADemo />} />
            </Routes>
          </Layout>
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
          />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
