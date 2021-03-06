//===-- AppleGetQueuesHandler.h ----------------------------*- C++ -*-===//
//
//                     The LLVM Compiler Infrastructure
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//

#ifndef lldb_AppleGetQueuesHandler_h_
#define lldb_AppleGetQueuesHandler_h_

// C Includes
// C++ Includes
#include <map>
#include <mutex>
#include <vector>

// Other libraries and framework includes
// Project includes
#include "lldb/lldb-public.h"
#include "lldb/Core/Error.h"
#include "lldb/Symbol/CompilerType.h"

// This class will insert a UtilityFunction into the inferior process for
// calling libBacktraceRecording's introspection_get_dispatch_queues()
// function.  The function in the inferior will return a struct by value
// with these members:
//
//     struct get_current_queues_return_values
//     {
//         introspection_dispatch_queue_info_t *queues_buffer;
//         uint64_t queues_buffer_size;
//         uint64_t count;
//     };
//
// The queues_buffer pointer is an address in the inferior program's address
// space (queues_buffer_size in size) which must be mach_vm_deallocate'd by
// lldb.  count is the number of queues that were stored in the buffer.
//
// The AppleGetQueuesHandler object should persist so that the UtilityFunction
// can be reused multiple times.

namespace lldb_private
{

class AppleGetQueuesHandler {
public:

    AppleGetQueuesHandler (lldb_private::Process *process);

    ~AppleGetQueuesHandler();

    struct GetQueuesReturnInfo
    {
        lldb::addr_t    queues_buffer_ptr;  /* the address of the queues buffer from libBacktraceRecording */
        lldb::addr_t    queues_buffer_size; /* the size of the queues buffer from libBacktraceRecording */
        uint64_t        count;              /* the number of queues included in the queues buffer */

        GetQueuesReturnInfo() :
            queues_buffer_ptr(LLDB_INVALID_ADDRESS),
            queues_buffer_size(0),
            count(0)
        {}
    };

    //----------------------------------------------------------
    /// Get the list of queues that exist (with any active or pending items) via
    /// a call to introspection_get_dispatch_queues().  If there's a page of
    /// memory that needs to be freed, pass in the address and size and it will
    /// be freed before getting the list of queues.
    ///
    /// @param [in] thread
    ///     The thread to run this plan on.
    ///
    /// @param [in] page_to_free
    ///     An address of an inferior process vm page that needs to be deallocated,
    ///     LLDB_INVALID_ADDRESS if this is not needed.
    ///
    /// @param [in] page_to_free_size
    ///     The size of the vm page that needs to be deallocated if an address was
    ///     passed in to page_to_free.
    ///
    /// @param [out] error
    ///     This object will be updated with the error status / error string from any failures encountered.
    ///
    /// @returns
    ///     The result of the inferior function call execution.  If there was a failure of any kind while getting
    ///     the information, the queues_buffer_ptr value will be LLDB_INVALID_ADDRESS.
    //----------------------------------------------------------
    GetQueuesReturnInfo
    GetCurrentQueues (Thread &thread, lldb::addr_t page_to_free, uint64_t page_to_free_size, lldb_private::Error &error);


    void
    Detach ();

private:

    lldb::addr_t
    SetupGetQueuesFunction (Thread &thread, ValueList &get_queues_arglist);

    static const char *g_get_current_queues_function_name;
    static const char *g_get_current_queues_function_code;

    lldb_private::Process *m_process;
    std::unique_ptr<UtilityFunction> m_get_queues_impl_code_up;
    std::mutex m_get_queues_function_mutex;

    lldb::addr_t m_get_queues_return_buffer_addr;
    std::mutex m_get_queues_retbuffer_mutex;
};

}  // using namespace lldb_private

#endif	// lldb_AppleGetQueuesHandler_h_
