# RuiderCar v7.1.5

1. Light mode input controls now use clearer borders, focus rings, labels, placeholder contrast, and number-input controls.
2. Opening a product from the browse page records the source listing and existing browse state.
3. Product detail adds “返回瀏覽位置”; returning restores the prior page/filter state and scrolls the source product back into view.
4. Product image bytes use a bounded in-process LRU cache to reduce repeated PostgreSQL image reads during page switching.
5. No database schema change.
