import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  DocumentTextIcon,
  FolderIcon,
  ChartBarIcon,
  FilmIcon,
  UserIcon,
  HomeIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Cases', href: '/cases', icon: FolderIcon },
  { name: 'Evidence', href: '/evidence', icon: DocumentTextIcon },
  { name: 'Storyboards', href: '/storyboards', icon: ChartBarIcon },
  { name: 'Renders', href: '/renders', icon: FilmIcon },
  { name: 'Profile', href: '/profile', icon: UserIcon },
];

export const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col lg:pt-16">
      <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white border-r border-gray-200 px-6 pb-4">
        <nav className="flex flex-1 flex-col">
          <ul role="list" className="flex flex-1 flex-col gap-y-7">
            <li>
              <ul role="list" className="-mx-2 space-y-1">
                {navigation.map((item) => {
                  const isActive = location.pathname.startsWith(item.href);
                  return (
                    <li key={item.name}>
                      <NavLink
                        to={item.href}
                        className={`sidebar-link ${
                          isActive ? 'sidebar-link-active' : 'sidebar-link-inactive'
                        }`}
                      >
                        <item.icon className="w-5 h-5 mr-3" />
                        {item.name}
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  );
};
