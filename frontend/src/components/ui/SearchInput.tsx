// frontend/src/components/ui/SearchInput.tsx
import React from 'react';
import { Icons } from './icons';
import './../../styles/components/search-input.css';

interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  fullWidth?: boolean;
}

export const SearchInput: React.FC<SearchInputProps> = ({
  fullWidth = true,
  className = '',
  ...props
}) => {
  const SearchIcon = Icons.Search;

  return (
    <div className={`search-input-wrapper ${fullWidth ? 'w-full' : ''} ${className}`.trim()}>
      <div className="search-icon">
        <SearchIcon />
      </div>
      <input
        type="text"
        className="search-input"
        {...props}
      />
    </div>
  );
};