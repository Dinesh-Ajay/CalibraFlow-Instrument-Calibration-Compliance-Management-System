import React from 'react';

const StatusBadge = ({ status }) => {
  if (!status) return null;

  const s = String(status).toUpperCase();

  let variant = ''; // default red .tg
  let label = status;

  if (['VALID', 'CALIBRATED', 'ALLOWED', 'SCHEDULED', 'CLOSED', 'PASS', 'COMPLETED', 'VERIFIED', 'RESOLVED', 'ACTIVE'].includes(s)) {
    variant = 'g'; // green
  } else if (['EXTENSION', 'DUE SOON', 'DUE_SOON', 'FLAGGED', 'MISSING', 'OPEN', 'PENDING', 'WARNING', 'MEDIUM', 'HIGH'].includes(s)) {
    variant = 'y'; // yellow
  } else if (['IN PROGRESS', 'IN_PROGRESS', 'ASSIGNED', 'RECORDED', 'LOW'].includes(s)) {
    variant = 'b'; // blue
  } else {
    variant = ''; // red (BLOCKED, OVERDUE, FAILED, FAIL, CRITICAL, EXPIRED, WRONG ASSET, REJECTED, INVALID)
  }

  return (
    <span className={`tg ${variant}`}>
      {label}
    </span>
  );
};

export default StatusBadge;
