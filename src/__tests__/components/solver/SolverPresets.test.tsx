import React from 'react';
import { render, screen, fireEvent } from '../../test-utils';
import { PresetSelector, PresetType, presets } from '../../../components/solver/SolverPresets';

describe('PresetSelector Component', () => {
  const mockOnSelectPreset = jest.fn();
  const selectedPreset: PresetType = 'balanced';

  beforeEach(() => {
    mockOnSelectPreset.mockClear();
  });

  it('renders all preset options', () => {
    render(
      <PresetSelector 
        selectedPreset={selectedPreset} 
        onSelectPreset={mockOnSelectPreset} 
      />
    );

    // Check that all preset names are displayed
    Object.values(presets).forEach(preset => {
      expect(screen.getByText(preset.name)).toBeInTheDocument();
    });
  });

  it('highlights the selected preset', () => {
    render(
      <PresetSelector 
        selectedPreset={selectedPreset} 
        onSelectPreset={mockOnSelectPreset} 
      />
    );

    // Check that the selected preset has the highlight class
    const selectedPresetElement = screen.getByText(presets[selectedPreset].name).closest('div');
    expect(selectedPresetElement).toHaveClass('bg-blue-100');

    // Check that other presets do not have the highlight class
    Object.keys(presets)
      .filter(key => key !== selectedPreset)
      .forEach(key => {
        const presetElement = screen.getByText(presets[key as PresetType].name).closest('div');
        expect(presetElement).not.toHaveClass('bg-blue-100');
      });
  });

  it('calls onSelectPreset when a preset is clicked', () => {
    render(
      <PresetSelector 
        selectedPreset={selectedPreset} 
        onSelectPreset={mockOnSelectPreset} 
      />
    );

    // Click on the 'strict' preset
    fireEvent.click(screen.getByText(presets.strict.name));
    expect(mockOnSelectPreset).toHaveBeenCalledWith('strict');

    // Click on the 'teacher' preset
    fireEvent.click(screen.getByText(presets.teacher.name));
    expect(mockOnSelectPreset).toHaveBeenCalledWith('teacher');
  });
});
