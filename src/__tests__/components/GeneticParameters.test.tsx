import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { GeneticParameters } from '../../components/GeneticParameters';
import type { GeneticSolverConfig } from '../../types';

describe('GeneticParameters Component', () => {
  // Default genetic configuration for testing
  const defaultConfig: GeneticSolverConfig = {
    enabled: true,
    populationSize: 100,
    eliteSize: 2,
    mutationRate: 0.1,
    crossoverRate: 0.8,
    maxGenerations: 100
  };

  test('does not render when not enabled', () => {
    const handleChange = jest.fn();
    const { container } = render(
      <GeneticParameters 
        config={{ ...defaultConfig, enabled: false }} 
        onChange={handleChange} 
      />
    );
    
    // Should render nothing
    expect(container.firstChild).toBeNull();
  });

  test('renders all parameters when enabled', () => {
    const handleChange = jest.fn();
    render(
      <GeneticParameters 
        config={defaultConfig} 
        onChange={handleChange} 
      />
    );
    
    // Check for all parameter labels
    expect(screen.getByText('Population Size')).toBeInTheDocument();
    expect(screen.getByText('Elite Size')).toBeInTheDocument();
    expect(screen.getByText('Mutation Rate')).toBeInTheDocument();
    expect(screen.getByText('Crossover Rate')).toBeInTheDocument();
    expect(screen.getByText('Max Generations')).toBeInTheDocument();
    
    // Check that values are displayed - using more specific queries to avoid duplicate matches
    const populationSizeLabel = screen.getByText('Population Size');
    expect(populationSizeLabel.closest('.bg-gray-50')).toHaveTextContent('100');
    
    const eliteSizeLabel = screen.getByText('Elite Size');
    expect(eliteSizeLabel.closest('.bg-gray-50')).toHaveTextContent('2');
    
    const mutationRateLabel = screen.getByText('Mutation Rate');
    expect(mutationRateLabel.closest('.bg-gray-50')).toHaveTextContent('0.1');
    
    const crossoverRateLabel = screen.getByText('Crossover Rate');
    expect(crossoverRateLabel.closest('.bg-gray-50')).toHaveTextContent('0.8');
    
    const maxGenerationsLabel = screen.getByText('Max Generations');
    expect(maxGenerationsLabel.closest('.bg-gray-50')).toHaveTextContent('100');
  });

  test('calls onChange when slider is adjusted', () => {
    const handleChange = jest.fn();
    render(
      <GeneticParameters 
        config={defaultConfig} 
        onChange={handleChange} 
      />
    );
    
    // Find the population size slider (first range input)
    const inputs = screen.getAllByRole('slider');
    const populationSlider = inputs[0];
    
    // Change its value
    fireEvent.change(populationSlider, { target: { value: '200' } });
    
    // Check that onChange was called with updated config
    expect(handleChange).toHaveBeenCalledWith({
      ...defaultConfig,
      populationSize: 200
    });
  });

  test('displays parameter descriptions', () => {
    const handleChange = jest.fn();
    render(
      <GeneticParameters 
        config={defaultConfig} 
        onChange={handleChange} 
      />
    );
    
    // Check for description texts
    expect(screen.getByText('Number of schedules in each generation')).toBeInTheDocument();
    expect(screen.getByText('Number of best schedules to keep')).toBeInTheDocument();
    expect(screen.getByText('Probability of random schedule changes')).toBeInTheDocument();
    expect(screen.getByText('Probability of combining schedules')).toBeInTheDocument();
    expect(screen.getByText('Maximum number of evolution cycles')).toBeInTheDocument();
  });
});
