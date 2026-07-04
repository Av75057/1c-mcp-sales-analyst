import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../../src/shared/components/ui/Button';
import { Badge } from '../../src/shared/components/ui/Badge';
import { Card, CardHeader, CardTitle, CardContent } from '../../src/shared/components/ui/Card';
import { Dialog } from '../../src/shared/components/ui/Dialog';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeTruthy();
  });

  it('calls onClick', () => {
    let clicked = false;
    render(<Button onClick={() => { clicked = true; }}>Click</Button>);
    fireEvent.click(screen.getByText('Click'));
    expect(clicked).toBe(true);
  });

  it('renders disabled', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByText('Disabled')).toBeTruthy();
  });

  it('renders with different variants', () => {
    const { container } = render(<Button variant="destructive">Delete</Button>);
    expect(container.querySelector('button')).toBeTruthy();
  });

  it('renders with different sizes', () => {
    const { container } = render(<Button size="sm">Small</Button>);
    expect(container.querySelector('button')).toBeTruthy();
  });
});

describe('Badge', () => {
  it('renders with text', () => {
    render(<Badge>Test</Badge>);
    expect(screen.getByText('Test')).toBeTruthy();
  });

  it('renders with variants', () => {
    const { container } = render(<Badge variant="success">OK</Badge>);
    expect(container.querySelector('span')).toBeTruthy();
  });
});

describe('Card', () => {
  it('renders card structure', () => {
    render(
      <Card>
        <CardHeader><CardTitle>Title</CardTitle></CardHeader>
        <CardContent>Content</CardContent>
      </Card>
    );
    expect(screen.getByText('Title')).toBeTruthy();
    expect(screen.getByText('Content')).toBeTruthy();
  });
});

describe('Dialog', () => {
  it('renders when open', () => {
    render(<Dialog open={true} onClose={() => {}} title="Modal Title"><p>Content</p></Dialog>);
    expect(screen.getByText('Modal Title')).toBeTruthy();
    expect(screen.getByText('Content')).toBeTruthy();
  });

  it('does not render when closed', () => {
    const { container } = render(<Dialog open={false} onClose={() => {}} title="Hidden"><p>Nope</p></Dialog>);
    expect(container.querySelector('.fixed')).toBeNull();
  });

  it('renders overlay', () => {
    render(<Dialog open={true} onClose={() => {}}><p>Test</p></Dialog>);
    expect(document.querySelector('.fixed')).toBeTruthy();
  });
});
