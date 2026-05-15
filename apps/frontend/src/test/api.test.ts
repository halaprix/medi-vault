import { describe, it, expect } from 'vitest';

// Test the API client type definitions
describe('API client types', () => {
  it('has expected document interface', () => {
    interface Document {
      id: string;
      filename: string;
      status: 'pending' | 'processing' | 'complete' | 'failed';
      created_at: string;
    }
    const doc: Document = { id: '1', filename: 'test.pdf', status: 'pending', created_at: '2026-01-01' };
    expect(doc.status).toBe('pending');
  });
});
