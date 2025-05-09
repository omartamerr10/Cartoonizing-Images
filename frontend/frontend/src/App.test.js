import { render, screen } from '@testing-library/react';
import App from './App';

test('renders image cartoonizer title', () => {
  render(<App />);
  const titleElement = screen.getByText(/Image Cartoonizer/i);
  expect(titleElement).toBeInTheDocument();
});

test('renders upload button', () => {
  render(<App />);
  const uploadButton = screen.getByText(/Upload Image/i);
  expect(uploadButton).toBeInTheDocument();
});
