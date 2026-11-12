import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Landing from "./pages/Landing";
import { Login, Register, Forgot, Reset } from "./pages/AuthPages";
import Dashboard from "./pages/Dashboard";
import MyTrips from "./pages/MyTrips";
import CreateTrip from "./pages/CreateTrip";
import JoinTrip from "./pages/JoinTrip";
import Settings from "./pages/Settings";
import TripLayout from "./pages/TripLayout";
import TripFund from "./pages/TripFund";
import Contributions from "./pages/Contributions";
import Expenses from "./pages/Expenses";
import AIAssistant from "./pages/AIAssistant";
import Statement from "./pages/Statement";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<Forgot />} />
      <Route path="/reset-password" element={<Reset />} />
      <Route path="/app" element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="trips" element={<MyTrips />} />
          <Route path="trips/new" element={<CreateTrip />} />
          <Route path="join" element={<JoinTrip />} />
          <Route path="settings" element={<Settings />} />
          <Route path="trips/:tripId" element={<TripLayout />}>
            <Route index element={<TripFund />} />
            <Route path="contributions" element={<Contributions />} />
            <Route path="expenses" element={<Expenses />} />
            <Route path="ai" element={<AIAssistant />} />
            <Route path="statement" element={<Statement />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
