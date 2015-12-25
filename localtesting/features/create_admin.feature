Feature: Create admin
    In order to allow for admin creation
    As super admin
    We will test the creation, activation, verification and login handler

    Scenario: create admin
        Given I am on the super_admin page
        When I add add 'test@example.com'
        Then I should see 'test@example.com'
        
As a super_admin
I should be able to add an admin account
So they can activate their account

As an admin
I should be able to activate my account
So I can proceed to verification

As an admin
I should be able to verify my account
So I can login

As and admin
I should be able to login
So I can navigate the site


Feature: Compute factorial
    In order to play with Lettuce
    As beginners
    We'll implement factorial

    Scenario: Factorial of 0
        Given I have the number 0
        When I compute its factorial
        Then I see the number 1