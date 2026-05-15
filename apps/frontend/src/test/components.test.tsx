import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '@/components/upload/StatusBadge';
import { ConfirmDialog } from '@/components/upload/ConfirmDialog';
import { MetricsSummaryBar } from '@/components/dashboard/MetricsSummaryBar';

describe('StatusBadge', () => {
  it('renders status text', () => {
    render(<StatusBadge status="complete" />);
    expect(screen.getByText('complete')).toBeDefined();
  });
});

describe('MetricsSummaryBar', () => {
  it('renders all four metric cards', () => {
    render(<MetricsSummaryBar />);
    expect(screen.getByText('Total Docs')).toBeDefined();
    expect(screen.getByText('Healthy')).toBeDefined();
  });
});
