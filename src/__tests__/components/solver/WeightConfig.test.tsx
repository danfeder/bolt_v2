import React from 'react';
import { render, screen, fireEvent } from '../../test-utils';
import { WeightConfig } from '../../../components/solver/WeightConfig';
import type { SolverWeights } from '../../../types';

describe('WeightConfig Component', () => {
  const mockChangeWeight = jest.fn();
  const testWeights: SolverWeights = {
    final_week_compression: 3000,
    day_usage: 2000,
    daily_balance: 1500,
    preferred_periods: 1000,
    distribution: 1000,
    avoid_periods: -500,
    earlier_dates: 10,
  };

  beforeEach(() => {
    mockChangeWeight.mockClear();
  });

  it('renders all weight sliders correctly', () => {
    render(
      <WeightConfig 
        weights={testWeights} 
        onChangeWeight={mockChangeWeight} 
      />
    );

    // Check for key weight settings
    expect(screen.getByText('Daily Balance')).toBeInTheDocument();
    expect(screen.getByText('Even Class Spread')).toBeInTheDocument();
    expect(screen.getByText('Preferred Times')).toBeInTheDocument();
    expect(screen.getByText('Avoid Conflicts')).toBeInTheDocument();
  });

  it('displays the correct weight values', () => {
    render(
      <WeightConfig 
        weights={testWeights} 
        onChangeWeight={mockChangeWeight} 
      />
    );

    // Check that the component displays the correct values
    // Using getAllByText since these values might appear multiple times
    expect(screen.getAllByText('1500')[0]).toBeInTheDocument(); // daily_balance
    expect(screen.getAllByText('1000')[0]).toBeInTheDocument(); // distribution
    expect(screen.getByText('-500')).toBeInTheDocument(); // avoid_periods
  });

  it('calls onChangeWeight when a slider is adjusted', () => {
    render(
      <WeightConfig 
        weights={testWeights} 
        onChangeWeight={mockChangeWeight} 
      />
    );

    // Find a slider by its id instead of label
    const distributionSlider = screen.getByTestId('setting-distribution');
    fireEvent.change(distributionSlider, { target: { value: '2000' } });

    // Check that the change handler was called with the correct values
    expect(mockChangeWeight).toHaveBeenCalledWith('distribution', 2000);
  });

  it('disables all sliders when disabled prop is true', () => {
    render(
      <WeightConfig 
        weights={testWeights} 
        onChangeWeight={mockChangeWeight} 
        disabled={true}
      />
    );

    // Check that all sliders are disabled
    const sliders = screen.getAllByRole('slider');
    sliders.forEach(slider => {
      expect(slider).toBeDisabled();
    });
  });
});
