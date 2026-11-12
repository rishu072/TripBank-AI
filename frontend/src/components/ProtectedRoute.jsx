import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth";
import { Loading } from "./ui";

export default function ProtectedRoute() {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <Loading />;
  return user ? <Outlet /> : <Navigate to="/login" state={{ from: loc.pathname + loc.search }} replace />;
}
