import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Catalog from "./pages/Catalog";
import AnimeDetail from "./pages/AnimeDetail";
import MyList from "./pages/MyList";
import Discover from "./pages/Discover";
import ForYou from "./pages/ForYou";

function Layout({ children }) {
  return (
    <>
      <Navbar />
      <main>{children}</main>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Layout><Login /></Layout>} />
          <Route path="/register" element={<Layout><Register /></Layout>} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout><Catalog /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/anime/:id"
            element={
              <ProtectedRoute>
                <Layout><AnimeDetail /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/my-list"
            element={
              <ProtectedRoute>
                <Layout><MyList /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/discover"
            element={
              <ProtectedRoute>
                <Layout><Discover /></Layout>
              </ProtectedRoute>
            }
          />
          <Route
            path="/for-you"
            element={
              <ProtectedRoute>
                <Layout><ForYou /></Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
