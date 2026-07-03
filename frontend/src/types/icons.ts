// frontend/src/types/icons.ts
/**
 * Icon type definitions for FPO360 Design System
 */

import { IconName, IconComponent } from '../components/ui/icons'

export type { IconName, IconComponent }

export interface IconProps extends React.SVGProps<SVGSVGElement> {
  /** Icon name from the centralized registry */
  name: IconName
  /** Size in pixels (default: 20) */
  size?: number
  /** Additional className for styling */
  className?: string
}