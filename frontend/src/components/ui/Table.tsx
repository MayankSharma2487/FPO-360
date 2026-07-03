// frontend/src/components/ui/Table.tsx
import React from 'react';
import { Icons, type IconName } from './icons';
import './../../styles/components/table.css';


interface TableProps {
  children: React.ReactNode;
  className?: string;
}

interface TableHeaderProps {
  children: React.ReactNode;
}

interface TableBodyProps {
  children: React.ReactNode;
}

interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  children: React.ReactNode;
  isSelected?: boolean;
}

interface TableHeadProps extends React.ThHTMLAttributes<HTMLTableCellElement> {
  children: React.ReactNode;
  sortable?: boolean;
}

interface TableCellProps extends React.TdHTMLAttributes<HTMLTableCellElement> {
  children: React.ReactNode;
}

interface TableEmptyProps {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  icon?: IconName;
}

interface TableLoadingProps {
  rows?: number;
  columns?: number;
}

interface TableToolbarProps {
  children: React.ReactNode;
}

export const Table: React.FC<TableProps> = ({ children, className = '' }) => (
  <div className={`table-container table-scroll ${className}`.trim()}>
    <table className="table">{children}</table>
  </div>
);

export const TableHeader: React.FC<TableHeaderProps> = ({ children }) => (
  <thead className="table-header">
    <tr>{children}</tr>
  </thead>
);

export const TableBody: React.FC<TableBodyProps> = ({ children }) => (
  <tbody className="table-body">{children}</tbody>
);

export const TableRow: React.FC<TableRowProps> = ({ 
  children, 
  isSelected = false, 
  className = '',
  ...props 
}) => (
  <tr 
    className={`table-row ${isSelected ? 'table-selected' : ''} ${className}`.trim()}
    {...props}
  >
    {children}
  </tr>
);

export const TableHead: React.FC<TableHeadProps> = ({ 
  children, 
  sortable = false,
  className = '',
  ...props 
}) => (
  <th 
    className={`table-cell table-head ${sortable ? 'table-sortable' : ''} ${className}`.trim()}
    {...props}
  >
    {children}
  </th>
);

export const TableCell: React.FC<TableCellProps> = ({ 
  children, 
  className = '',
  ...props 
}) => (
  <td 
    className={`table-cell ${className}`.trim()}
    {...props}
  >
    {children}
  </td>
);

export const TableEmpty: React.FC<TableEmptyProps> = ({
  title = "No records found",
  description = "There are no items to display at the moment.",
  action,
  icon = 'Package'
}) => {
  const IconComponent = Icons[icon as keyof typeof Icons];
  
  return (
    <tr>
      <td colSpan={100} className="table-empty">
        <div className="empty-state">
          {IconComponent && <IconComponent className="empty-icon" />}
          <div className="empty-title">{title}</div>
          <div className="empty-description">{description}</div>
          {action && <div className="empty-action">{action}</div>}
        </div>
      </td>
    </tr>
  );
};

export const TableLoading: React.FC<TableLoadingProps> = ({ 
  rows = 5, 
  columns = 6 
}) => (
  <tbody className="table-loading">
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <tr key={rowIndex} className="table-row">
        {Array.from({ length: columns }).map((_, colIndex) => (
          <td key={colIndex} className="table-cell">
            <div className="table-skeleton" />
          </td>
        ))}
      </tr>
    ))}
  </tbody>
);

export const TableToolbar: React.FC<TableToolbarProps> = ({ children }) => (
  <div className="table-toolbar">{children}</div>
);