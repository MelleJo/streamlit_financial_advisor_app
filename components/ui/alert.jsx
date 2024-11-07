import React from 'react';

export const Alert = ({ children, className, ...props }) => {
  return (
    <div className={`alert ${className}`} {...props}>
      {children}
    </div>
  );
};

export const AlertDescription = ({ children, className, ...props }) => {
  return (
    <div className={`alert-description ${className}`} {...props}>
      {children}
    </div>
  );
};
