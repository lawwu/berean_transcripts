#!/bin/bash

# Import necessary functions and variables from bash_transcribe_new_videos.sh
source "../bash_transcribe_new_videos.sh"

# Import necessary functions and variables from bash_transcribe_new_videos.sh
source "../bash_transcribe_new_videos.sh"

# Test SSH agent setup and key addition

test_bcc_live_video_ids_not_empty() {
    touch bcc_live_video_ids.txt

    # Call the function to be tested
    start_ssh_agent_and_add_ssh_key()

    # Assert the expected output
    assert_true "$(ls $SCRIPT_DIR/data/bcc_live_video_ids.txt)" "bcc_live_video_ids.txt exists"

    # Run all the tests
    run_tests
}
test_ssh_agent_setup_and_key_addition() {
    # Mock SSH agent setup and key addition
    mock_ssh_agent_start() {
        echo "SSH agent setup"
    }
    ssh-add() {
        mock_ssh_agent_start
        echo "SSH key added"
    }

    # Call the function to be tested
    start_ssh_agent_and_add_ssh_key()

    # Assert the expected output
    assert_true "$(eval ssh-add)" "SSH agent is running"
    # For example:
    # assert_equal "$(eval)" "SSH agent setup"
    # assert_equal "$(ssh-add)" "SSH key added"
}

# Run the unit tests
test_ssh_agent_setup_and_key_addition

# Test case to check if the SSH agent is started
mock_ssh_agent_start() {

# Assert the necessary files are added and committed
    assert_true "$(grep 'git add' bash_transcribe_new_videos.sh)" "Files are added"
    assert_true "$(grep 'AUTO: adding latest messages' bash_transcribe_new_videos.sh)" "Files are committed"

    # Run all the tests
run_tests
