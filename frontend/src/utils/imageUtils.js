export const getScaledImageDimensions = (imgRef) => {
  const imgElement = imgRef.current;
  if (imgElement) {
    return {
      width: imgElement.clientWidth,
      height: imgElement.clientHeight,
      naturalWidth: imgElement.naturalWidth,
      naturalHeight: imgElement.naturalHeight,
    };
  }
  return { width: 0, height: 0, naturalWidth: 0, naturalHeight: 0 };
};

export const spinnerKeyframes = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;