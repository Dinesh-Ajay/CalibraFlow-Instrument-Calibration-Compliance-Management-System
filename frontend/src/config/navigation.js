import {
  LayoutDashboard,
  Kanban,
  Gauge,
  CalendarDays,
  FileCheck2,
  Wrench,
  Factory,
  BellRing,
  History,
  ShieldCheck,
  Users,
  KeyRound,
  Boxes,
} from 'lucide-react';

/**
 * Official Role-Based Navigation Policy Matrix
 * Module                Admin  Quality  Maint  Operator  Planner
 * Dashboard              YES    YES     YES      YES       YES
 * Workflow Board         YES    YES     YES      NO        YES
 * Instruments            YES    YES     YES      YES       YES
 * Plans & Events         YES    YES     YES      NO        YES
 * Certificates           YES    YES     YES      NO        NO
 * Work Orders            YES    YES     YES      NO        YES
 * Production Use         YES    YES     YES      YES       YES
 * Alerts                 YES    YES     YES      YES       YES
 * Audit Trail            YES    YES     NO       NO        NO
 * Data Quality           YES    YES     NO       NO        NO
 * User Management        YES    NO      NO       NO        NO
 * Roles & Permissions    YES    NO      NO       NO        NO
 * Instrument Types       YES    NO      NO       NO        NO
 */

export const ROLE_ALIASES = {
  admin: ['admin', 'Administrator'],
  quality_eng: ['quality_eng', 'Quality Engineer'],
  maint_eng: ['maint_eng', 'Maintenance Engineer'],
  operator: ['operator', 'Plant Operator'],
  planner: ['planner', 'Production Planner'],
};

export const NAVIGATION_MODULES = [
  {
    id: 'dashboard',
    to: '/',
    label: 'Dashboard',
    icon: LayoutDashboard,
    allowedRoles: [
      'admin', 'Administrator',
      'quality_eng', 'Quality Engineer',
      'maint_eng', 'Maintenance Engineer',
      'operator', 'Plant Operator',
      'planner', 'Production Planner',
    ],
  },
  {
    id: 'workflow-board',
    to: '/workflow-board',
    label: 'Workflow board',
    icon: Kanban,
    allowedRoles: [
      'admin', 'Administrator',
      'quality_eng', 'Quality Engineer',
      'maint_eng', 'Maintenance Engineer',
      'planner', 'Production Planner',
    ],
  },
  {
    id: 'instruments',
    to: '/instruments',
    label: 'Instruments',
    icon: Gauge,
    allowedRoles: [
      'admin', 'Administrator',
      'quality_eng', 'Quality Engineer',
      'maint_eng', 'Maintenance Engineer',
      'operator', 'Plant Operator',
      'planner', 'Production Planner',
    ],
  },
  {
    id: 'plans-events',
    to: '/plans-events',
    label: 'Plans and events',
    icon: CalendarDays,
    allowedRoles: [
      'admin', 'Administrator',
      'quality_eng', 'Quality Engineer',
      'maint_eng', 'Maintenance Engineer',
      'planner', 'Production Planner',
    ],
  },
  {
    id: 'certificates',
    to: '/certificates',
    label: 'Certificates',
    icon: FileCheck2,
    allowedRoles: [
      'admin', 'Administrator',
      'quality_eng', 'Quality Engineer',
      'maint_eng', 'Maintenance Engineer',
    ],
  },
  {
    id: 'work-orders',
    to: '/work-orders',
    label: 'Work orders',
    icon: Wrench,
    allowedRoles: [
      'admin', 'Administrator',
      'quality_eng', 'Quality Engineer',
      'maint_eng', 'Maintenance Engineer',
      'planner', 'Production Planner',
    ],
  },
  {
    id: 'production-use',
    to: '/production-use',
    label: 'Production use',
    icon: Factory,
    allowedRoles: [
      'admin', 'Administrator',
      'quality_eng', 'Quality Engineer',
      'maint_eng', 'Maintenance Engineer',
      'operator', 'Plant Operator',
      'planner', 'Production Planner',
    ],
  },
  {
    id: 'alerts',
    to: '/alerts',
    label: 'Alerts',
    icon: BellRing,
    allowedRoles: [
      'admin', 'Administrator',
      'quality_eng', 'Quality Engineer',
      'maint_eng', 'Maintenance Engineer',
      'operator', 'Plant Operator',
      'planner', 'Production Planner',
    ],
  },
  {
    id: 'audit',
    to: '/audit',
    label: 'Audit trail',
    icon: History,
    allowedRoles: [
      'admin', 'Administrator',
      'quality_eng', 'Quality Engineer',
    ],
  },
  {
    id: 'data-quality',
    to: '/data-quality',
    label: 'Data quality',
    icon: ShieldCheck,
    allowedRoles: [
      'admin', 'Administrator',
      'quality_eng', 'Quality Engineer',
    ],
  },
  {
    id: 'user-management',
    to: '/admin/users',
    label: 'User management',
    icon: Users,
    allowedRoles: [
      'admin', 'Administrator',
    ],
  },
  {
    id: 'roles-permissions',
    to: '/admin/roles',
    label: 'Roles & permissions',
    icon: KeyRound,
    allowedRoles: [
      'admin', 'Administrator',
    ],
  },
  {
    id: 'instrument-types',
    to: '/admin/instrument-types',
    label: 'Instrument types',
    icon: Boxes,
    allowedRoles: [
      'admin', 'Administrator',
    ],
  },
];

export const isModuleAllowed = (moduleIdOrPath, userRoles = []) => {
  if (!userRoles || !userRoles.length) return false;
  // Administrator always has access to all modules
  if (userRoles.includes('Administrator') || userRoles.includes('admin')) {
    return true;
  }
  const mod = NAVIGATION_MODULES.find(
    (m) => m.id === moduleIdOrPath || m.to === moduleIdOrPath
  );
  if (!mod) return false;
  return mod.allowedRoles.some((role) => userRoles.includes(role));
};

export const getPermittedNavItems = (userRoles = []) => {
  if (!userRoles || !userRoles.length) return [];
  if (userRoles.includes('Administrator') || userRoles.includes('admin')) {
    return NAVIGATION_MODULES;
  }
  return NAVIGATION_MODULES.filter((item) =>
    item.allowedRoles.some((role) => userRoles.includes(role))
  );
};
