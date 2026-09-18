import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./layouts/AppShell";
import { DashboardPage } from "./pages/DashboardPage";
import { ResourcePage } from "./pages/ResourcePage";
import { TripCreatePage } from "./pages/TripCreatePage";
import { LrCreatePage } from "./pages/LrCreatePage";
import { CollectionPage } from "./pages/CollectionPage";
import { FinancePage } from "./pages/FinancePage";
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

function Guard({ children, perm }: { children: React.ReactNode; perm?: string }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "PLATFORM_SUPER_ADMIN") return <AppShell>{children}</AppShell>;
  if (perm && !can(user.permissions, perm)) return <PermissionDenied />;
  return <AppShell>{children}</AppShell>;
}

function Hub({ title, links }: { title: string; links: { to: string; label: string }[] }) {
  return (
    <section>
      <h1 className="h1">{title}</h1>
      <div className="grid kpis">
        {links.map((l) => (
          <a key={l.to} className="card" href={l.to}>
            {l.label}
          </a>
        ))}
      </div>
    </section>
  );
}

export function AppRoutes({ onLogin }: { onLogin: (token: string, user: unknown) => void }) {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage onLogin={onLogin} />} />
      <Route path="/" element={<Guard perm="dashboard:read"><DashboardPage /></Guard>} />
      <Route path="/trips" element={<Guard perm="trip:read"><TripsPage /></Guard>} />
      <Route path="/trips/new" element={<Guard perm="trip:create"><TripCreatePage /></Guard>} />
      <Route path="/trips/:id" element={<Guard perm="trip:read"><RecordDetailPage resource="trips" /></Guard>} />
      <Route path="/lrs/new" element={<Guard perm="lr:create"><LrCreatePage /></Guard>} />
      <Route path="/lrs/:id" element={<Guard perm="lr:read"><RecordDetailPage resource="lrs" /></Guard>} />
      <Route path="/fleet" element={<Guard><Hub title="Fleet" links={[{ to: "/vehicles", label: "Vehicles" }, { to: "/maintenance", label: "Maintenance" }, { to: "/fuel-providers", label: "Fuel pumps" }]} /></Guard>} />
      <Route path="/people" element={<Guard><Hub title="People" links={[{ to: "/drivers", label: "Drivers" }, { to: "/employees", label: "Employees" }, { to: "/handovers", label: "Handover" }]} /></Guard>} />
      <Route path="/vehicles" element={<Guard perm="vehicle:read"><ResourcePage title="Vehicles" resource="vehicles" columns={[{ key: "vehicle_number", label: "Number" }, { key: "vehicle_type", label: "Type" }, { key: "status", label: "Status" }]} createFields={[{ key: "vehicle_number", label: "Vehicle number" }, { key: "vehicle_type", label: "Type" }, { key: "make", label: "Make" }]} /></Guard>} />
      <Route path="/vehicles/:id" element={<Guard perm="vehicle:read"><RecordDetailPage resource="vehicles" /></Guard>} />
      <Route path="/drivers" element={<Guard perm="driver:read"><ResourcePage title="Drivers" resource="drivers" columns={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "status", label: "Status" }]} createFields={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "licence_number", label: "Licence" }]} /></Guard>} />
      <Route path="/drivers/:id" element={<Guard perm="driver:read"><RecordDetailPage resource="drivers" /></Guard>} />
      <Route path="/employees" element={<Guard perm="employee:read"><ResourcePage title="Employees" resource="employees" columns={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "role_name", label: "Role" }, { key: "status", label: "Status" }]} createFields={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "role_name", label: "Role" }]} /></Guard>} />
      <Route path="/parties" element={<Guard perm="party:read"><ResourcePage title="Parties" resource="parties" columns={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "city", label: "City" }, { key: "status", label: "Status" }]} createFields={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }, { key: "city", label: "City" }]} /></Guard>} />
      <Route path="/parties/:id" element={<Guard perm="party:read"><RecordDetailPage resource="parties" /></Guard>} />
      <Route path="/locations" element={<Guard perm="location:read"><ResourcePage title="Locations" resource="locations" columns={[{ key: "name", label: "Name" }, { key: "city", label: "City" }, { key: "type", label: "Type" }, { key: "status", label: "Status" }]} createFields={[{ key: "name", label: "Name" }, { key: "city", label: "City" }, { key: "type", label: "Type" }]} /></Guard>} />
      <Route path="/routes" element={<Guard perm="route:read"><ResourcePage title="Routes" resource="routes" columns={[{ key: "name", label: "Name" }, { key: "origin_name", label: "From" }, { key: "destination_name", label: "To" }]} createFields={[{ key: "name", label: "Name" }, { key: "origin_name", label: "Origin" }, { key: "destination_name", label: "Destination" }]} /></Guard>} />
      <Route path="/fuel-providers" element={<Guard perm="fuel:read"><ResourcePage title="Fuel pumps" resource="fuel-providers" columns={[{ key: "name", label: "Name" }, { key: "location", label: "Location" }]} createFields={[{ key: "name", label: "Name" }, { key: "location", label: "Location" }]} /></Guard>} />
      <Route path="/partners" element={<Guard perm="partner:read"><ResourcePage title="3PL partners" resource="partners" columns={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }]} createFields={[{ key: "name", label: "Name" }, { key: "mobile", label: "Mobile" }]} /></Guard>} />
      <Route path="/maintenance" element={<Guard perm="vehicle:read"><ResourcePage title="Maintenance" resource="maintenance" columns={[{ key: "description", label: "Work" }, { key: "cost", label: "Cost" }]} createFields={[{ key: "vehicle_id", label: "Vehicle ID" }, { key: "description", label: "Description" }, { key: "cost", label: "Cost" }]} /></Guard>} />
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
