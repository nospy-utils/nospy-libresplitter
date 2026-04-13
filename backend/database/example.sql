insert into expenses (user_created, currency, value, description) VALUES (1,'NZD',10.00, 'CD 1');
insert into expense_user (expense_id, from_user_id, to_user_id, value) VALUES (1,1,2,5.0);
insert into expenses (user_created, currency, value, description) VALUES (1,'NZD',20.00, 'CD 2');
insert into expense_user (expense_id, from_user_id, to_user_id, value) VALUES (2,1,2,10.0);
insert into expenses (user_created, currency, value, description) VALUES (1,'NZD',30.00, 'CD 3');
insert into expense_user (expense_id, from_user_id, to_user_id, value) VALUES (3,1,2,15.0);
insert into expenses (user_created, currency, value, description) VALUES (1,'NZD',40.00, 'CD 4');
insert into expense_user (expense_id, from_user_id, to_user_id, value) VALUES (4,1,2,20.0);
insert into expenses (user_created, currency, value, description) VALUES (1,'BRL',50.00, 'Cach 1');
insert into expense_user (expense_id, from_user_id, to_user_id, value) VALUES (5,1,2,25.0);
insert into expenses (user_created, currency, value, description) VALUES (1,'BRL',60.00, 'Cach 2');
insert into expense_user (expense_id, from_user_id, to_user_id, value) VALUES (6,1,2,30.0);
insert into expenses (user_created, currency, value, description) VALUES (2,'NZD',10.00, 'CD 5');
insert into expense_user (expense_id, from_user_id, to_user_id, value) VALUES (7,2,1,5.0);
insert into expenses (user_created, currency, value, description) VALUES (3,'NZD',90.00, 'churras');
insert into expense_user (expense_id, from_user_id, to_user_id, value) VALUES (8,3,1,30.0);
insert into expense_user (expense_id, from_user_id, to_user_id, value) VALUES (8,3,2,30.0);

 -- returns how my I owe /am owed
SELECT
  e.currency,
  SUM(CASE WHEN eu.from_user_id = 3 THEN eu.value ELSE -eu.value END) AS my_total
FROM expenses e
INNER JOIN expense_user eu ON e.id = eu.expense_id
WHERE eu.from_user_id = 3 OR eu.to_user_id = 3
GROUP BY e.currency;

-- returns expenses grouped by friend -
SELECT
  CASE WHEN eu.from_user_id = 3 THEN eu.to_user_id ELSE eu.from_user_id END AS friend_id,
  e.currency,
  SUM(CASE WHEN eu.from_user_id = 3 THEN eu.value ELSE -eu.value END) AS net_total
FROM expenses e
INNER JOIN expense_user eu ON e.id = eu.expense_id
WHERE eu.from_user_id = 3 OR eu.to_user_id = 3
GROUP BY friend_id, e.currency;

