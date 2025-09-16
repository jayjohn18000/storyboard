import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline';

export const Breadcrumbs: React.FC = () => {
  const location = useLocation();
  
  const pathSegments = location.pathname.split('/').filter(Boolean);
  
  const getBreadcrumbName = (segment: string, index: number) => {
    // Handle dynamic routes
    if (segment.match(/^[a-f0-9-]{36}$/)) {
      return 'Case Details'; // UUID pattern for case IDs
    }
    
    // Handle specific route names
    switch (segment) {
      case 'cases':
        return 'Cases';
      case 'evidence':
        return 'Evidence';
      case 'storyboards':
        return 'Storyboards';
      case 'renders':
        return 'Renders';
      case 'profile':
        return 'Profile';
      default:
        return segment.charAt(0).toUpperCase() + segment.slice(1);
    }
  };

  if (pathSegments.length === 0) {
    return null;
  }

  return (
    <nav className="flex mb-6" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2">
        <li>
          <Link to="/cases" className="text-gray-400 hover:text-gray-500">
            <HomeIcon className="w-4 h-4" />
            <span className="sr-only">Home</span>
          </Link>
        </li>
        
        {pathSegments.map((segment, index) => {
          const isLast = index === pathSegments.length - 1;
          const href = '/' + pathSegments.slice(0, index + 1).join('/');
          const name = getBreadcrumbName(segment, index);
          
          return (
            <li key={segment}>
              <div className="flex items-center">
                <ChevronRightIcon className="w-4 h-4 text-gray-400 mx-2" />
                {isLast ? (
                  <span className="text-sm font-medium text-gray-500">{name}</span>
                ) : (
                  <Link
                    to={href}
                    className="text-sm font-medium text-gray-500 hover:text-gray-700"
                  >
                    {name}
                  </Link>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
