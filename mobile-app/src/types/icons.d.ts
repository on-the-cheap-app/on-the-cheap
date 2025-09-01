declare module 'react-native-vector-icons/MaterialCommunityIcons' {
  import React from 'react';
  import { TextProps } from 'react-native';

  interface IconProps extends TextProps {
    name: string;
    size?: number;
    color?: string;
  }

  const Icon: React.ComponentType<IconProps>;
  export default Icon;
}