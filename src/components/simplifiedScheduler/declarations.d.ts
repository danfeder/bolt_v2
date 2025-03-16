/**
 * Type declarations for simplified scheduler components
 */

// Declare modules for our component files to resolve TypeScript errors
declare module './PriorityList' {
  import { FC } from 'react';
  import { Priority } from './types';
  
  export interface PriorityListProps {
    priorities: Priority[];
    onReorder: (newPriorities: Priority[]) => void;
    disabled?: boolean;
  }
  
  export const PriorityList: FC<PriorityListProps>;
}

declare module './InstructorLoadSettings' {
  import { FC } from 'react';
  import { InstructorLoadSettings } from './types';
  
  export interface InstructorLoadProps {
    settings: InstructorLoadSettings;
    onChange: (changes: Partial<InstructorLoadSettings>) => void;
    disabled?: boolean;
  }
  
  export const InstructorLoadSettings: FC<InstructorLoadProps>;
}

declare module './AdvancedOptions' {
  import { FC } from 'react';
  import { AdvancedSettings } from './types';
  
  export interface AdvancedOptionsProps {
    settings: AdvancedSettings;
    onChange: (changes: Partial<AdvancedSettings>) => void;
    disabled?: boolean;
  }
  
  export const AdvancedOptions: FC<AdvancedOptionsProps>;
}
