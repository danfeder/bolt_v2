import React from 'react';
import { screen, fireEvent, cleanup } from '@testing-library/react';
import { render } from '../../test-utils';
import { SolverConfigPanel } from '../../../components/solver/SolverConfigPanel';
import type { SolverWeights, GeneticSolverConfig } from '../../../types';

// Define an interface for our mock state
interface MockState {
  geneticConfig: GeneticSolverConfig;
  isGenerating: boolean;
  setGeneticConfig: (config: Partial<GeneticSolverConfig>) => void;
}

// Define a type for the selector function
type SelectorFunction = (state: MockState) => any;

// Mock the store
jest.mock('../../../store/scheduleStore', () => ({
  useScheduleStore: jest.fn()
}));

// Import the mocked module
const mockedScheduleStore = jest.requireMock('../../../store/scheduleStore');

// Create default mock values to use across tests
const defaultGeneticConfig: GeneticSolverConfig = {
  enabled: false,
  populationSize: 100,
  eliteSize: 2,
  mutationRate: 0.1,
  crossoverRate: 0.8,
  maxGenerations: 100
};

describe('SolverConfigPanel Component', () => {
  const mockSetGeneticConfig = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Set up our mock store implementation with a stable function reference
    mockedScheduleStore.useScheduleStore.mockImplementation((selector: SelectorFunction | undefined) => {
      // Define our mock state with stable references
      const mockState: MockState = {
        geneticConfig: {...defaultGeneticConfig},
        isGenerating: false,
        setGeneticConfig: mockSetGeneticConfig
      };
      
      // Handle selectors
      if (typeof selector === 'function') {
        return selector(mockState);
      }
      return mockState;
    });
  });

  afterEach(() => {
    cleanup();
    jest.resetAllMocks();
  });

  test('renders all configuration sections', () => {
    render(<SolverConfigPanel />);
    
    // Check main heading
    expect(screen.getByText('Solver Configuration')).toBeInTheDocument();
    
    // Check for preset selector
    expect(screen.getByText('Configuration Presets')).toBeInTheDocument();
    
    // Check for weight config section
    expect(screen.getByText('Solver Weights')).toBeInTheDocument();
    
    // Check for genetic config section
    expect(screen.getByText('🧬 Genetic Algorithm')).toBeInTheDocument();
  });

  test('selecting a preset updates configuration', () => {
    render(<SolverConfigPanel />);
    
    // Find and click the strict requirements preset
    const strictPreset = screen.getByText('Strict Requirements');
    fireEvent.click(strictPreset);
    
    // Now we only expect setGeneticConfig to be called when a preset has genetic settings
    expect(mockSetGeneticConfig).toHaveBeenCalled();
  });

  test('changing a weight does not update the store', () => {
    render(<SolverConfigPanel />);
    
    // Find a slider and change its value
    const distributionSlider = screen.getByTestId('setting-distribution');
    fireEvent.change(distributionSlider, { target: { value: '2000' } });
    
    // We no longer expect setGeneticConfig to be called for weight changes
    expect(mockSetGeneticConfig).not.toHaveBeenCalled();
  });

  test('enabling genetic algorithm updates the genetic config', () => {
    render(<SolverConfigPanel />);
    
    // Find the genetic toggle and enable it
    const geneticToggle = screen.getByRole('checkbox');
    fireEvent.click(geneticToggle);
    
    // Check that setGeneticConfig was called
    expect(mockSetGeneticConfig).toHaveBeenCalled();
    
    // Check that it was called with the enabled property set to true
    expect(mockSetGeneticConfig).toHaveBeenCalledWith(expect.objectContaining({
      enabled: true
    }));
  });

  test('displays lockout message when generating', () => {
    // Update the mock for this specific test to show generating state
    mockedScheduleStore.useScheduleStore.mockImplementation((selector: SelectorFunction | undefined) => {
      // Mock state with isGenerating=true
      const mockGeneratingState: MockState = {
        geneticConfig: {...defaultGeneticConfig},
        isGenerating: true,
        setGeneticConfig: mockSetGeneticConfig
      };
      
      // Handle selectors
      if (typeof selector === 'function') {
        return selector(mockGeneratingState);
      }
      return mockGeneratingState;
    });
    
    render(<SolverConfigPanel />);
    
    // Check for lockout message
    expect(screen.getByText(/Configuration is locked while generating/)).toBeInTheDocument();
    
    // Weight sliders should be disabled
    const distributionSlider = screen.getByTestId('setting-distribution');
    expect(distributionSlider).toBeDisabled();
  });
});
