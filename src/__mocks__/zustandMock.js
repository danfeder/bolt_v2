// Mock for Zustand store
export const createMockStore = (initialState) => {
  const store = {
    ...initialState,
    getState: () => store,
    setState: (updater) => {
      if (typeof updater === 'function') {
        Object.assign(store, updater(store));
      } else {
        Object.assign(store, updater);
      }
    },
    subscribe: jest.fn(),
    destroy: jest.fn(),
  };

  return store;
};
