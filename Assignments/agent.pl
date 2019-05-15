%*****************************************************************%
% Team: Subham Anand, z5151878                                    %
%       Bharadwaj Varanasi, z5154500                              %
%                                                                 %
% Course: Artificial Intelligence - COMP9414                      %
%                                                                 %
% Assignment: Assignment3-Navigating a Simulated Environment,     %
%             Option 2: Prolog(BDI Agent)                         %
%                                                                 %
% Prolog(BDI Agent): This involves implementing the basic         %
%                    functions of a simple BDI agent operating    %
%                    in a GridWorld Environment.                  %
%                                                                 %
%*****************************************************************%

%******************************************************************
% initial_intentions(Intentions)
%
% which binds Intentions to intents(L,[]) with L in the form
% [[goal(X1,Y1),[]], ... , [goal(Xn,Yn),[]]]. Here (Xn,Yn) is
% the location of the monster and (X1,Y1), ... , (Xn-1,Yn-1)
% are places where the mininum number of stones
% need to be dropped in order to allow the agent to move
% along some path from its current location to that of
% the monster.
%*****************************************************************

% base case: no legs to be inserted
insert_legs(Generated, [], Generated).

% Insert the first leg using insert_one_leg(); and continue.
insert_legs(Generated, [Leg|Legs], Generated2) :-
   insert_one_leg(Generated, Leg, Generated1),
   insert_legs(Generated1, Legs, Generated2).

% head_member(Node, List)
% check whether Node is the head of a member of List.

% base case: node is the head of first item in list.
head_member(Node,[[Node,_]|_]).

% otherwise, keep searching for node in the tail.
head_member(Node,[_|Tail]) :-
  head_member(Node,Tail).

% build_path(Expanded, [[Node,Pred]], Path).

% build_path(Legs, Path)
% Construct a path from a list of legs, by joining the ones that match.

% base case: join the last two legs to form a path of one step.
build_path([[Next,Start],[Start,Start]], [Next,Start]).

% If the first two legs match, add to the front of the path.
build_path([[C,B],[B,A]|Expanded],[C,B,A|Path]) :-
   build_path([[B,A]|Expanded],[B,A|Path]), ! .

% If the above rule fails, we skip the next leg in the list.
build_path([Leg,_SkipLeg|Expanded],Path) :-
   build_path([Leg|Expanded],Path).


goal(Pos) :-
    length(Pos,10),
    goal3(Pos).

goal3([10/10,1/1,1/2,1/3,1/4,1/5,1/6,1/7,1/8,1/9,1/10,
      2/1,2/2,2/3,2/4,2/5,2/6,2/7,2/8,2/9,2/10,
      3/1,3/2,3/3,3/4,3/5,3/6,3/7,3/8,3/9,3/10,
      4/1,4/2,4/3,4/4,4/5,4/6,4/7,4/8,4/9,4/10,
      5/1,5/2,5/3,5/4,5/5,5/6,5/7,5/8,5/9,5/10,
      6/1,6/2,6/3,6/4,6/5,6/6,6/7,6/8,6/9,6/10,
      7/1,7/2,7/3,7/4,7/5,7/6,7/7,7/8,7/9,7/10,
      8/1,8/2,8/3,8/4,8/5,8/6,8/7,8/8,8/9,8/10,
      9/1,9/2,9/3,9/4,9/5,9/6,9/7,9/8,9/9,9/10,
      10/1,10/2,10/3,10/4,10/5,10/6,10/7,10/8,10/9]).


%*****************************************************************%
%                                                                 %
% Trigger(Percepts, Goals):                                       %
%                                                                 %
% which takes a list of percepts, each of the form stone(X,Y),    %
% and converts it into a corresponding list of goals,             %
% each of the form goal(X,Y).                                     %
%                                                                 %
%*****************************************************************%

trigger([], []).
trigger([stone(X, Y)|Tail], [goal(X, Y)|Goals]) :-
    trigger(Tail, Goals).


%----------------------------------

% Base case, no more Goals.
incorporate_goals([], Intentions, Intentions).

% Goal is already in the Intentions list so skip it.
incorporate_goals([NewGoal|Tail_Goal], Intentions, Intentions1) :-
    check_goal(NewGoal, Intentions),
    incorporate_goals(Tail_Goal, Intentions, Intentions1).

% We only insert if its not already in the Intentions list.
incorporate_goals([NewGoal|Tail_Goal], Intentions, Intentions1) :-
    not(check_goal(NewGoal, Intentions)),
    insert_goal(NewGoal, Intentions, Update_Intentions),
    incorporate_goals(Tail_Goal, Update_Intentions, Intentions1).

%----------------------------------

%-----------------------------------

check_goal(TempGoal, [Head_int|_]) :-
    member(TempGoal, Head_int).

check_goal(TempGoal, [Head_int|Tail_int]) :-
    not(member(TempGoal, Head_int)),
	check_goal(TempGoal, Tail_int).

%-----------------------------------

%-----------------------------------

insert_goal(Goal, [Intent|Intentions], [Intent|Intentions1]):-
    not(gtp(Goal, Intent)), !,
    insert_goal(Goal, Intentions, Intentions1).

insert_goal(X, Intentions, [[X, []]|Intentions]).

%------------------------------------

%------------------------------------


% Compare distances to Belief.
gtp(goal(X1, Y1), [goal(X2, Y2)|_], [at(X, Y)|_]) :-
    distance((X, Y), (X1, Y1), D1),
    distance((X, Y), (X2, Y2), D2),
    D1 < D2.

%------------------------------------

%******************************************************************%
%                                                                  %
%                                                                  %
% update_intentions(Observation, Intentions, Intentions1)          %
%                                                                  %
% which takes a list of percepts, each of the form                 %
% stone(X,Y), % and converts it into a corresponding               %
% list of goals, each of the form goal(X,Y).                       %
%                                                                  %
% *****************************************************************%

update_intentions(cleaned(X, Y), [[goal(X, Y)|_]|Intentions1], Intentions1).

% catch the rest to stop backtracking.
update_intentions(_, Intentions, Intentions).

