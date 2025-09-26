import os
import sys
import time
from rl_agent.environment import SumoEnvironment
from rl_agent.agent import QLearningAgent

def test_environment_basic():
    """Test that the environment can start and run basic operations."""
    print("🧪 Testing SUMO Environment...")
    
    try:
        # Create environment (no GUI for testing)
        env = SumoEnvironment(use_gui=False, simulation_step=10)
        
        # Test reset
        print("   ✅ Environment created successfully")
        state = env.reset()
        print(f"   ✅ Environment reset, initial state: {state}")
        
        # Test a few steps
        print("   🔄 Testing environment steps...")
        for i in range(5):
            action = 0 if i < 3 else 1  # Keep phase first, then switch
            next_state, reward, wait_time = env.step(action)
            print(f"      Step {i+1}: Action={action}, Reward={reward:.2f}, Wait={wait_time:.1f}")
        
        # Test performance metrics
        metrics = env.get_performance_metrics()
        print(f"   📊 Performance metrics: {metrics['total_vehicles']} vehicles, {metrics['total_queue']} queued")
        
        # Clean up
        env.close()
        print("   ✅ Environment test passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Environment test failed: {e}")
        return False

def test_agent_basic():
    """Test that the Q-learning agent works correctly."""
    print("🧪 Testing Q-Learning Agent...")
    
    try:
        # Create agent
        agent = QLearningAgent(
            state_size=3,
            action_size=2,
            learning_rate=0.1,
            epsilon_start=0.8
        )
        print("   ✅ Agent created successfully")
        
        # Test action selection
        test_state = [1, 2, 0]  # Medium NS, High EW, NS phase
        action = agent.choose_action(test_state)
        print(f"   ✅ Action selection works: {action}")
        
        # Test learning
        next_state = [0, 1, 1]  # Low NS, Medium EW, EW phase
        reward = -1.0
        agent.learn(test_state, action, reward, next_state)
        print("   ✅ Learning step completed")
        
        # Test Q-value retrieval
        q_value = agent.get_q_value(test_state, action)
        print(f"   ✅ Q-value retrieval: {q_value:.3f}")
        
        # Test stats
        stats = agent.get_stats()
        print(f"   📊 Agent stats: {stats['total_states_learned']} states learned")
        
        print("   ✅ Agent test passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Agent test failed: {e}")
        return False

def test_training_loop():
    """Test a mini training loop to verify everything works together."""
    print("🧪 Testing Mini Training Loop...")
    
    try:
        # Create environment and agent
        env = SumoEnvironment(use_gui=False, simulation_step=10)
        agent = QLearningAgent(state_size=3, action_size=2, learning_rate=0.2)
        
        print("   🚀 Starting mini training (5 episodes, 60 seconds each)...")
        
        for episode in range(3):  # Just 3 episodes for testing
            state = env.reset()
            total_reward = 0
            steps = 0
            
            # Run episode for 60 seconds (6 steps at 10s each)
            for step in range(6):
                action = agent.choose_action(state)
                next_state, reward, wait_time = env.step(action)
                agent.learn(state, action, reward, next_state)
                
                state = next_state
                total_reward += reward
                steps += 1
            
            print(f"   Episode {episode+1}: Reward={total_reward:.1f}, Steps={steps}")
        
        # Print final stats
        agent.print_stats()
        env.close()
        
        print("   ✅ Mini training loop test passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Training loop test failed: {e}")
        if 'env' in locals():
            env.close()
        return False

def check_sumo_installation():
    """Check if SUMO is properly installed."""
    print("🧪 Checking SUMO Installation...")
    
    if 'SUMO_HOME' not in os.environ:
        print("   ❌ SUMO_HOME environment variable not set!")
        print("   📝 Please install SUMO and set SUMO_HOME")
        return False
    
    sumo_home = os.environ['SUMO_HOME']
    print(f"   📁 SUMO_HOME: {sumo_home}")
    
    sumo_binary = os.path.join(sumo_home, 'bin', 'sumo')
    if not os.path.exists(sumo_binary):
        print(f"   ❌ SUMO binary not found at {sumo_binary}")
        return False
    
    print("   ✅ SUMO installation looks good!")
    return True

def run_all_tests():
    """Run all tests to verify the system is ready."""
    print("🚦 SUMO RL System Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: SUMO installation
    if check_sumo_installation():
        tests_passed += 1
    print()
    
    # Test 2: Environment
    if test_environment_basic():
        tests_passed += 1
    print()
    
    # Test 3: Agent
    if test_agent_basic():
        tests_passed += 1
    print()
    
    # Test 4: Training loop
    if test_training_loop():
        tests_passed += 1
    print()
    
    # Results
    print("=" * 50)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("✨ All tests passed! System is ready for training.")
        print("🚀 Run 'python train.py' to start full training!")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        print("💡 Make sure SUMO is properly installed and configured.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    print("Starting training system tests...")
    success = run_all_tests()
    
    if success:
        print("\n🎉 Ready to train! Here's what you can do next:")
        print("   1. Run: python train.py (full 50-episode training)")
        print("   2. Run: python train.py (modify episodes/settings as needed)")
        print("   3. Check training_log.csv for detailed results")
        print("   4. View training_progress.png for performance graphs")
    else:
        print("\n🔧 Please fix the issues above before training.")
    
    sys.exit(0 if success else 1)