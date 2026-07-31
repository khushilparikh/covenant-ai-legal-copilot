import React from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import { AuthProvider } from "./context/AuthContext";
import { BillingProvider } from "./context/BillingContext";
import Chat from "./pages/Chat";
import Checkout from "./pages/Checkout";
import Compliance from "./pages/Compliance";
import Comparison from "./pages/Comparison";
import ContractDetail from "./pages/ContractDetail";
import ContractsList from "./pages/ContractsList";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import Upload from "./pages/Upload";

export default function App() {
  return (
    <AuthProvider>
      <BillingProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route element={<AppLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/contracts" element={<ContractsList />} />
              <Route path="/contracts/:id" element={<ContractDetail />} />
              <Route path="/upload" element={<Upload />} />
              <Route path="/compliance" element={<Compliance />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/comparison" element={<Comparison />} />
              <Route path="/profile" element={<Profile />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </BillingProvider>
    </AuthProvider>
  );
}
