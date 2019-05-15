% Subham Anand
% Z5151878
% Assignment 1 Prolog Programming

% Question 1

% Base Case
sumsq_neg([], 0).

% Check if the Head is less than 0 then calculate its square and add it
% to sum
sumsq_neg([H|T], S) :-
    sumsq_neg(T, S1),
    H < 0 ,
    S is S1 + (H*H).

% If head is empty then add 0, will do nothing.
sumsq_neg([_|T], S) :-
    sumsq_neg(T, S1),
    S is S1 + 0.


% Question 2

% Base case for the helper predicate
all_likes(_, []).

% This is helper predicate, it will check for a particular name that
% whether he like all the fruits or not.
all_likes(Name, [H2|T2]) :-
    all_likes(Name, T2),
    likes(Name, H2).


% Base case for the predicate.
all_like_all([], _).

% It will take one name at a time and pass it to all_likes helper
% predicate.
all_like_all([H|T], L) :-
    all_like_all(T, L),
    all_likes(H, L).


% Question 3

% This will run till N is greater than M and will do the square root and
% put it into the list.
sqrt_table(N, M, Result):-
    N > M,
    X is sqrt(N),
    L = [[N, X]],
    Y is N-1,
    sqrt_table(Y, M, New),
    append(L, New , Result).

% This is one seperate case when N becomes equalt to M.
sqrt_table(N, M, Result):-
    N=:=M,
    Y is sqrt(N),
    Result = [[N, Y]].

% Question 4

% This is helper predicate if the list is having only first element.
enter(List, Mid, Back):-
    List = [E|[]],
    Mid is E,
    append([],[],Back).

% This is helper predicate if the second element is not successive we will
% put everything to the list and keep track of the element (Mid) till
% where it reached. (Back) will have all the remaining elements to be
% checked
enter(List, Mid, Back):-
    List = [A, B|C],
    B =\= A+1,
    Mid is A,
    append([B],C,Back).

% This is the helper predicate if second element is successive we will
% put everything to the list and keep track of the element (Mid) till
% where it reached. (Back) will have all the remaining elements to be
% checked
enter(List, Mid, Back):-
    List = [A, B|C],
    B is A+1,
    enter([B|C], Temp_Mid, Temp_Back),
    Mid = Temp_Mid,
    Back = Temp_Back.

% Base case
chop_up([],[]).

% If the (Mid) itself is the next element means it has not travesed
% forward so keep that element only.
chop_up(List, Result):-
    Result = [H|T],
    List = [F|_],
    enter(List, Mid, Back),
    F is Mid,
    H is F,
    chop_up(Back, T).

% If (Mid) is not the first element from where it started looking then
% put the first element and the last till where we looked or traversed.
chop_up(List, Result):-
    Result = [H|T],
    List = [F|_],
    enter(List, Mid, Back),
    F =\= Mid,
    H = [F, Mid],
    chop_up(Back, T).

% Question 5

% Base case to get Value as Eval
tree_eval(Value, tree(empty, z, empty), Value).

% Base case to put the Number as Eval
tree_eval(_, tree(empty, N, empty), N).

% It will traverse the left tree with the eval and then right tree with
% the eval and then calculate the expression using the operator.
tree_eval(Value, tree(Left, Op, Right), Eval):-
    tree_eval(Value, Left, Leftval),
    tree_eval(Value, Right, Rightval),
    Evals =.. [Op, Leftval, Rightval],
    Eval is Evals.











