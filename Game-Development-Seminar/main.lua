-- set window size and resolution
VIRTUAL_WIDTH = 384
VIRTUAL_HEIGHT = 216
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

-- set paddle details
PADDLE_WIDTH = 8
PADDLE_HEIGHT = 32
PADDLE_SPEED = 140

BALL_SIZE = 4

-- set fonts
LARGE_FONT = love.graphics.newFont(32)
SMALL_FONT = love.graphics.newFont(16)

push = require 'push'

-- create player1 and player2 information (kinda like python classes)
player1 = {
    x = 10, 
    y = 10,
    score = 0
}

player2 = {
    x = VIRTUAL_WIDTH - 10 - PADDLE_WIDTH, 
    y = VIRTUAL_HEIGHT - 10 - PADDLE_HEIGHT,
    score = 0
}

ball = {
    x = VIRTUAL_WIDTH / 2 - BALL_SIZE / 2,
    y = VIRTUAL_HEIGHT / 2 - BALL_SIZE / 2,
    dx = 0, dy = 0
}

gameState = 'title'

function love.load()
    -- set up screen
    math.randomseed(os.time())
    love.graphics.setDefaultFilter('nearest', 'nearest')
    push:setupScreen(VIRTUAL_WIDTH, VIRTUAL_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT)
    -- set ball position and speed
    resetBall()
end

function love.update(dt)
    -- move paddles but can't move beyond edge of screen
    if love.keyboard.isDown('w') and player1.y > 0 then
        player1.y = player1.y - PADDLE_SPEED * dt
    elseif love.keyboard.isDown('s') and player1.y < VIRTUAL_HEIGHT - PADDLE_HEIGHT then
        player1.y = player1.y + PADDLE_SPEED * dt
    end
    if love.keyboard.isDown('up') and player2.y > 0 then
        player2.y = player2.y - PADDLE_SPEED * dt
    elseif love.keyboard.isDown('down') and player2.y < VIRTUAL_HEIGHT - PADDLE_HEIGHT then
        player2.y = player2.y + PADDLE_SPEED * dt
    end

    if gameState == 'play' then
        -- move ball when  in play mode
        ball.x = ball.x + ball.dx * dt
        ball.y = ball.y + ball.dy * dt

        -- score points if ball passes edge
        if ball.x <= 0 then
            player2.score = player2.score + 1
            resetBall()
            gameState = 'serve'
        elseif ball.x >= VIRTUAL_WIDTH - BALL_SIZE then
            player1.score = player1.score + 1
            resetBall()
            gameState = 'serve'
        end

        -- bounce off the edges
        if ball.y <= 0 or ball.y >= VIRTUAL_HEIGHT - BALL_SIZE then
            ball.dy = -ball.dy
        end

        -- reverse direction if collides with paddle
        if collides(player1, ball) then
            ball.dx = -ball.dx
            ball.x = player1.x + PADDLE_WIDTH
        elseif collides(player2, ball) then
            ball.dx = -ball.dx
            ball.x = player2.x -BALL_SIZE
        end
    end
end

function love.keypressed(key)
    -- end game if esc is pressed
    if key == 'escape' then
        love.event.quit()
    end

    -- go to the next state if enter is pressed
    if key == 'enter' or key == 'return' then
        if gameState == 'title' then
            gameState = 'serve'
        elseif gameState == 'serve' then
            gameState = 'play'
        end
    end
end

function love.draw()
    push:start()
    love.graphics.clear(40/255, 45/255, 52/255, 255/255) -- set bg color

    -- set text for the beginning
    if gameState == 'title' then
        love.graphics.setFont(LARGE_FONT)
        love.graphics.printf('Pre50 Pong', 0, 10, VIRTUAL_WIDTH, 'center')
        love.graphics.setFont(SMALL_FONT)
        love.graphics.printf('Press Enter', 0, VIRTUAL_HEIGHT - 32, VIRTUAL_WIDTH, 'center')
    elseif gameState == 'serve' then
        love.graphics.setFont(SMALL_FONT)
        love.graphics.printf('Press Enter to Serve!', 0, 10, VIRTUAL_WIDTH, 'center')
    end

    -- set fonts and score
    love.graphics.setFont(LARGE_FONT)
    love.graphics.print(player1.score, VIRTUAL_WIDTH / 2 - 36, VIRTUAL_HEIGHT / 2 - 16)
    love.graphics.print(player2.score, VIRTUAL_WIDTH / 2 + 16, VIRTUAL_HEIGHT / 2 - 16)
    love.graphics.setFont(SMALL_FONT)

    love.graphics.rectangle('fill', player1.x, player1.y, PADDLE_WIDTH, PADDLE_HEIGHT) -- create paddle in upper left
    love.graphics.rectangle('fill', player2.x, player2.y, PADDLE_WIDTH, PADDLE_HEIGHT) -- create paddle in lower right
    love.graphics.rectangle('fill', ball.x, ball.y, BALL_SIZE, BALL_SIZE) -- create ball
    push:finish()
end

function resetBall()
    -- send ball to starting position
    ball.x = VIRTUAL_WIDTH / 2 - BALL_SIZE / 2
    ball.y = VIRTUAL_HEIGHT / 2 - BALL_SIZE / 2

    -- determine speed and direction
    ball.dx = 60 + math.random(60)
    if math.random(2) == 1 then
        ball.dx = -ball.dx
    end
    ball.dy = 30 + math.random(60)
    if math.random(2) == 1 then
        ball.dy = -ball.dy
    end
end

function collides(p, b)
    -- check if the ball has collided with one of the paddles
    return not (p.x > b.x + BALL_SIZE or p.y > b.y + BALL_SIZE or b.x > p.x + PADDLE_WIDTH or b.y > p.y + PADDLE_HEIGHT)
end