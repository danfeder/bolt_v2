import React from 'react';
import { render, screen, fireEvent } from '../../test-utils';
import { GeneticConfig } from '../../../components/solver/GeneticConfig';
import type { GeneticSolverConfig } from '../../../types';

describe('GeneticConfig Component', () => {
  const mockOnChange = jest.fn();
  const enabledConfig: GeneticSolverConfig = {
    enabled: true,
    populationSize: 200,
    eliteSize: 4,
    mutationRate: 0.1,
    crossoverRate: 0.8,
    maxGenerations: 100
  };
  
  const disabledConfig: GeneticSolverConfig = {
    ...enabledConfig,
    enabled: false
  };

  beforeEach(() => {
    mockOnChange.mockClear();
  });

  it('displays parameters when enabled', () => {
    render(
      <GeneticConfig 
        config={enabledConfig} 
        onChange={mockOnChange} 
      />
    );

    // Check for genetic algorithm parameters
    expect(screen.getByText('Population Size')).toBeInTheDocument();
    expect(screen.getByText('Elite Size')).toBeInTheDocument();
    expect(screen.getByText('Mutation Rate')).toBeInTheDocument();
    expect(screen.getByText('Crossover Rate')).toBeInTheDocument();
    expect(screen.getByText('Max Generations')).toBeInTheDocument();
  });

  it('hides parameters when disabled', () => {
    render(
      <GeneticConfig 
        config={disabledConfig} 
        onChange={mockOnChange} 
      />
    );

    // Parameters should not be visible when disabled
    expect(screen.queryByText('Population Size')).not.toBeInTheDocument();
    expect(screen.queryByText('Elite Size')).not.toBeInTheDocument();
  });

  it('calls onChange when toggling enabled state', () => {
    render(
      <GeneticConfig 
        config={enabledConfig} 
        onChange={mockOnChange} 
      />
    );

    // Find and click the toggle switch
    const toggleSwitch = screen.getByRole('checkbox');
    fireEvent.click(toggleSwitch);

    // Check that onChange was called with the correct parameter
    expect(mockOnChange).toHaveBeenCalledWith({ enabled: false });
  });

  it('calls onChange when adjusting a parameter slider', () => {
    render(
      <GeneticConfig 
        config={enabledConfig} 
        onChange={mockOnChange} 
      />
    );

    // Find the population size slider using testId
    const populationSlider = screen.getByTestId('genetic-populationSize');
    fireEvent.change(populationSlider, { target: { value: '300' } });

    // Check that onChange was called with the correct parameter
    expect(mockOnChange).toHaveBeenCalledWith({ populationSize: 300 });
  });

  it('disables all controls when disabled prop is true', () => {
    render(
      <GeneticConfig 
        config={enabledConfig} 
        onChange={mockOnChange}
        disabled={true}
      />
    );

    // Check that the toggle switch is disabled
    const toggleSwitch = screen.getByRole('checkbox');
    expect(toggleSwitch).toBeDisabled();

    // Check that all sliders are disabled
    const sliders = screen.getAllByRole('slider');
    sliders.forEach(slider => {
      expect(slider).toBeDisabled();
    });
  });
});
