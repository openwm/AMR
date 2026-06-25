Feature: Outbound order picking flow

  Background:
    Given the warehouse system is reset

  Scenario: AMR picks up inventory and delivers it to the pick station
    Given inventory is seeded for 2 products in warehouse locations
    When an outbound order is submitted with those products
    And planning allocates the inventory
    Then the order status is "ACTIVE"
    When the order is released to the warehouse control system
    Then the order status is "PICKING"
    When an AMR travels to each inventory location to collect the stock
    And the AMR delivers the stock to the pick station
    When the operator picks all items at the picking station
    Then the order status is "SHIPPED"
    And a shipped shipment exists for the order
