import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./layouts/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { MasterList } from "./pages/MasterList";
import { TripCreatePage } from "./pages/TripCreatePage";
import { LrCreatePage } from "./pages/LrCreatePage";
import { CollectionPage } from "./pages/CollectionPage";
import { FinancePage } from "./pages/FinancePage";
import { OwnerHome, RoleHome } from "./pages/RoleHome";
import {
  ExpensePage,
  FuelPage,
  HandoverPage,
  LoginPage,
  NotificationsPage,
  PlatformPage,
  RecordDetailPage,
  ReportsPage,
  SearchPage,
  SettingsPage,
  TripsPage,
} from "./pages/MiscPages";
import { useAuth, can } from "./auth";
import { PermissionDenied } from "./components/ui/primitives";
import { LOGIN_HIDDEN } from "./config";

function Guard({ children, perm }: { children: React.ReactNode; perm?: string }) {
  const { user } = useAuth();
  if (!user) return <Navigate to={LOGIN_HIDDEN ? "/" : "/login"} replace />;
  if (user.role === "PLATFORM_SUPER_ADMIN") return <AppShell>{children}</AppShell>;
  if (perm && !can(user.permissions, perm)) return <PermissionDenied />;
  return <AppShell>{children}</AppShell>;
}

export function AppRoutes({ onLogin }: { onLogin: (token: string, user: unknown) => void }) {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/" element={LOGIN_HIDDEN && !user ? <RoleHome onLogin={onLogin} /> : <Navigate to={user?.role === "PLATFORM_SUPER_ADMIN" ? "/platform" : "/home"} replace />} />
      <Route path="/login" element={LOGIN_HIDDEN ? <Navigate to="/" replace /> : <LoginPage onLogin={onLogin} />} />
      <Route path="/home" element={<Guard><OwnerHome /></Guard>} />
      <Route path="/ops" element={<Guard perm="dashboard:read"><DashboardPage /></Guard>} />
      <Route path="/trips" element={<Guard perm="trip:read"><TripsPage /></Guard>} />
      <Route path="/trips/new" element={<Guard perm="trip:create"><TripCreatePage /></Guard>} />
      <Route path="/trips/:id" element={<Guard perm="trip:read"><RecordDetailPage resource="trips" /></Guard>} />
      <Route path="/lrs" element={<Guard perm="lr:read"><MasterList title="LR" resource="lrs" createTo="/lrs/new" columns={[{ key: "lr_number", label: "LR" }, { key: "sender_name", label: "Sender" }, { key: "receiver_name", label: "Receiver" }, { key: "freight_type", label: "Freight" }, { key: "status", label: "Status" }]} fields={[{ key: "receiver_name", label: "Receiver" }]} createLabel="New LR" /></Guard>} />
      <Route path="/lrs/new" element={<Guard perm="lr:create"><LrCreatePage /></Guard>} />
      <Route path="/lrs/:id" element={<Guard perm="lr:read"><RecordDetailPage resource="lrs" /></Guard>} />
      <Route path="/vehicles" element={<Guard perm="vehicle:read"><MasterList title="Vehicle listing" resource="vehicles" columns={[{ key: "vehicle_number", label: "Number" }, { key: "make", label: "Make" }, { key: "model", label: "Model" }, { key: "vehicle_type", label: "Type" }, { key: "status", label: "Status" }]} fields={[{ key: "vehicle_number", label: "Vehicle number" }, { key: "make", label: "Make" }, { key: "model", label: "Model" }, { key: "vehicle_type", label: "Type" }]} /></Guard>} />
      <Route path="/vehicle-models" element={<Guard perm="vehicle:read"><MasterList title="Vehicle models" resource="vehicle-models" columns={[{ key: "make", label: "Make" }, { key: "model", label: "Model" }, { key: "status", label: "Status" }]} fields={[{ key: "make", label: "Make" }, { key: "model", label: "Model" }]} /></Guard>} />
      <Route path="/vehicles/:id" element={<Guard perm="vehicle:read"><RecordDetailPage resource="vehicles" /></Guard>} />
      <Route path="/drivers" element={<Guard perm="driver:read"><MasterList title="Drivers" resource="drivers" columns={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "role_name", label: "Role" }, { key: "status", label: "Status" }]} fields={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "licence_number", label: "Licence" }]} /></Guard>} />
      <Route path="/drivers/:id" element={<Guard perm="driver:read"><RecordDetailPage resource="drivers" /></Guard>} />
      <Route path="/employees" element={<Guard perm="employee:read"><MasterList title="Employees" resource="employees" columns={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "role_name", label: "Role" }, { key: "status", label: "Status" }]} fields={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "role_name", label: "Role" }]} /></Guard>} />
      <Route path="/parties" element={<Guard perm="party:read"><MasterList title="Client listing" resource="parties" columns={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "city", label: "City" }, { key: "status", label: "Status" }]} fields={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "city", label: "City" }]} /></Guard>} />
      <Route path="/parties/:id" element={<Guard perm="party:read"><RecordDetailPage resource="parties" /></Guard>} />
      <Route path="/locations" element={<Guard perm="location:read"><MasterList title="Locations" resource="locations" columns={[{ key: "name", label: "Name" }, { key: "city", label: "City" }, { key: "type", label: "Type" }, { key: "status", label: "Status" }]} fields={[{ key: "name", label: "Name" }, { key: "city", label: "City" }, { key: "type", label: "Type" }]} /></Guard>} />
      <Route path="/routes" element={<Guard perm="route:read"><MasterList title="Indoor routes" resource="routes" columns={[{ key: "name", label: "Name" }, { key: "origin_name", label: "From" }, { key: "destination_name", label: "To" }, { key: "status", label: "Status" }]} fields={[{ key: "name", label: "Name" }, { key: "origin_name", label: "Origin" }, { key: "destination_name", label: "Destination" }]} /></Guard>} />
      <Route path="/fuel-providers" element={<Guard perm="fuel:read"><MasterList title="Fuel pumps" resource="fuel-providers" columns={[{ key: "name", label: "Name" }, { key: "location", label: "Location" }]} fields={[{ key: "name", label: "Name" }, { key: "location", label: "Location" }]} /></Guard>} />
      <Route path="/partners" element={<Guard perm="partner:read"><MasterList title="3PL partners" resource="partners" columns={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }]} fields={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }]} /></Guard>} />
      <Route path="/finance" element={<Guard perm="finance:read"><FinancePage /></Guard>} />
      <Route path="/collections/new" element={<Guard perm="collection:create"><CollectionPage /></Guard>} />
      <Route path="/expenses/new" element={<Guard perm="expense:create"><ExpensePage /></Guard>} />
      <Route path="/fuel/new" element={<Guard perm="fuel:create"><FuelPage /></Guard>} />
      <Route path="/handovers" element={<Guard perm="collection:create"><HandoverPage /></Guard>} />
      <Route path="/reports" element={<Guard perm="report:read"><ReportsPage /></Guard>} />
      <Route path="/settings" element={<Guard perm="settings:read"><SettingsPage /></Guard>} />
      <Route path="/platform" element={<Guard perm="platform:tenants"><PlatformPage /></Guard>} />
      <Route path="/search" element={<Guard><SearchPage /></Guard>} />
      <Route path="/notifications" element={<Guard><NotificationsPage /></Guard>} />
    </Routes>
  );
}
