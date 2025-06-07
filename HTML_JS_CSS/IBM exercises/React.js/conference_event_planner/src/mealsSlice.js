// mealsSlice.js
import { createSlice } from '@reduxjs/toolkit';

export const mealsSlice = createSlice({
  name: 'meals',
  initialState: [
    {
      name: "Breakfast",
      cost: 25,
      selected: false,
      attendees: 0
    },
    {
      name: "Lunch",
      cost: 35,
      selected: false,
      attendees: 0
    },
    {
      name: "Dinner",
      cost: 45,
      selected: false,
      attendees: 0
    }
  ],
  reducers: {
    toggleMealSelection: (state, action) => {
      const { payload: index } = action;
      if (state[index]) {
        state[index].selected = !state[index].selected;
      }
    },
    setAttendees: (state, action) => {
      const { index, count } = action.payload;
      if (state[index]) {
        state[index].attendees = count;
      }
    }
  },
});

export const { toggleMealSelection, setAttendees } = mealsSlice.actions;

export default mealsSlice.reducer;
