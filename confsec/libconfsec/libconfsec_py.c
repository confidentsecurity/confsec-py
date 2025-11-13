#define PY_SSIZE_T_CLEAN

#include <stdlib.h>
#include <stdbool.h>
#include <Python.h>
#include "libconfsec.h"

#define PYFUNC(name) static PyObject* py_##name(PyObject* self, PyObject* args)
#define INIT_ERROR char* err = NULL;
#define HANDLE_ERROR(err)                         \
    if (err != NULL) {                            \
        PyErr_SetString(PyExc_RuntimeError, err); \
        free(err);                                \
        return NULL;                              \
    }

static PyObject* py_confsec_client_create(PyObject* self, PyObject* args) {
    INIT_ERROR;
    char* api_url;
    char* api_key;
    int identity_policy_source;
    char* oidc_issuer;
    char* oidc_issuer_regex;
    char* oidc_subject;
    char* oidc_subject_regex;
    int concurrent_requests_target;
    int max_candidate_nodes;
    PyObject* py_default_node_tags;
    const char** default_node_tags;
    size_t default_node_tags_count;
    char* env;
    uintptr_t handle;

    if (!PyArg_ParseTuple(args,
                          "ssissssiiOz",
                          &api_url,
                          &api_key,
                          &identity_policy_source,
                          &oidc_issuer,
                          &oidc_issuer_regex,
                          &oidc_subject,
                          &oidc_subject_regex,
                          &concurrent_requests_target,
                          &max_candidate_nodes,
                          &py_default_node_tags,
                          &env)) {
        return NULL;
    }

    if (!PyList_Check(py_default_node_tags)) {
        PyErr_SetString(PyExc_TypeError, "default_node_tags must be a list");
        return NULL;
    }

    default_node_tags_count = (size_t)(PyList_Size(py_default_node_tags));
    default_node_tags = PyMem_Malloc(default_node_tags_count * sizeof(const char*));

    for (size_t i = 0; i < default_node_tags_count; i++) {
        PyObject* py_tag = PyList_GetItem(py_default_node_tags, i);
        if (!PyUnicode_Check(py_tag)) {
            PyErr_SetString(PyExc_TypeError, "default_node_tags must be a list of strings");
            return NULL;
        }

        default_node_tags[i] = PyUnicode_AsUTF8(py_tag);
        if (default_node_tags[i] == NULL) {
            // Exception already set by PyUnicode_AsUTF8
            return NULL;
        }
    }

    handle = Confsec_ClientCreate(api_url,
                                  api_key,
                                  identity_policy_source,
                                  oidc_issuer,
                                  oidc_issuer_regex,
                                  oidc_subject,
                                  oidc_subject_regex,
                                  concurrent_requests_target,
                                  max_candidate_nodes,
                                  (char**)default_node_tags,
                                  default_node_tags_count,
                                  env,
                                  &err);

    HANDLE_ERROR(err);

    // In general, we expect an error to be returned if the handle is 0, but we should
    // check just in case and throw an exception if it is.
    if (handle == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Unexpected error creating client");
        return NULL;
    }

    PyMem_Free(default_node_tags);

    return PyLong_FromUnsignedLongLong(handle);
}

static PyObject* py_confsec_client_destroy(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    Confsec_ClientDestroy(handle, &err);

    HANDLE_ERROR(err);

    Py_RETURN_NONE;
}

static PyObject* py_confsec_client_get_default_credit_amount(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    long default_credit_amount;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    default_credit_amount = Confsec_ClientGetDefaultCreditAmountPerRequest(handle, &err);

    HANDLE_ERROR(err);

    return PyLong_FromLong(default_credit_amount);
}

static PyObject* py_confsec_client_get_max_candidate_nodes(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    int max_candidate_nodes;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    max_candidate_nodes = Confsec_ClientGetMaxCandidateNodes(handle, &err);

    HANDLE_ERROR(err);

    return PyLong_FromLong(max_candidate_nodes);
}

static PyObject* py_confsec_client_get_default_node_tags(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    char** default_node_tags;
    size_t default_node_tags_count;
    PyObject* py_default_node_tags;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    default_node_tags = Confsec_ClientGetDefaultNodeTags(handle, &default_node_tags_count, &err);
    HANDLE_ERROR(err);

    py_default_node_tags = PyList_New((Py_ssize_t)default_node_tags_count);
    for (size_t i = 0; i < default_node_tags_count; i++) {
        PyObject* py_tag = PyUnicode_FromString(default_node_tags[i]);
        PyList_SetItem(py_default_node_tags, i, py_tag);
    }

    return py_default_node_tags;
}

static PyObject* py_confsec_client_set_default_node_tags(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    PyObject* py_default_node_tags;
    const char** default_node_tags;
    size_t default_node_tags_count;

    if (!PyArg_ParseTuple(args, "KO", &handle, &py_default_node_tags)) {
        return NULL;
    }

    if (!PyList_Check(py_default_node_tags)) {
        PyErr_SetString(PyExc_TypeError, "default_node_tags must be a list");
        return NULL;
    }

    default_node_tags_count = (size_t)(PyList_Size(py_default_node_tags));
    default_node_tags = PyMem_Malloc(default_node_tags_count * sizeof(const char*));

    for (size_t i = 0; i < default_node_tags_count; i++) {
        PyObject* py_tag = PyList_GetItem(py_default_node_tags, i);
        if (!PyUnicode_Check(py_tag)) {
            PyErr_SetString(PyExc_TypeError, "default_node_tags must be a list of strings");
            return NULL;
        }

        default_node_tags[i] = PyUnicode_AsUTF8(py_tag);
        if (default_node_tags[i] == NULL) {
            // Exception already set by PyUnicode_AsUTF8
            return NULL;
        }
    }

    Confsec_ClientSetDefaultNodeTags(handle, (char**)default_node_tags, default_node_tags_count, &err);
    HANDLE_ERROR(err);

    PyMem_Free(default_node_tags);

    Py_RETURN_NONE;
}

static PyObject* py_confsec_client_get_wallet_status(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    char* wallet_status;
    PyObject* py_wallet_status;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    wallet_status = Confsec_ClientGetWalletStatus(handle, &err);
    HANDLE_ERROR(err);

    py_wallet_status = PyUnicode_FromString(wallet_status);

    Confsec_Free(wallet_status);

    return py_wallet_status;
}

static PyObject* py_confsec_client_do_request(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    char* request;
    Py_ssize_t request_length;
    uintptr_t response_handle;

    if (!PyArg_ParseTuple(args, "Ky#", &handle, &request, &request_length)) {
        return NULL;
    }

    response_handle = Confsec_ClientDoRequest(handle, request, request_length, &err);
    HANDLE_ERROR(err);

    // In general, we expect an error to be returned if the response is NULL, but we
    // should check just in case and throw an exception if it is.
    if (response_handle == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Unexpected request failure");
        return NULL;
    }

    return PyLong_FromUnsignedLongLong(response_handle);
}

static PyObject* py_confsec_response_destroy(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    Confsec_ResponseDestroy(handle, &err);
    HANDLE_ERROR(err);

    Py_RETURN_NONE;
}

static PyObject* py_confsec_response_get_metadata(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    char* metadata;
    PyObject* py_metadata;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    metadata = Confsec_ResponseGetMetadata(handle, &err);
    HANDLE_ERROR(err);

    // In general, we expect an error to be returned if the header is NULL, but we
    // should check just in case and throw an exception if it is.
    if (metadata == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Unexpected error getting request header");
        return NULL;
    }

    py_metadata = PyBytes_FromString(metadata);
    // PyBytes_FromString copies the underlying string, so we should free it here to
    // avoid a memory leak.
    Confsec_Free(metadata);

    return py_metadata;
}

static PyObject* py_confsec_response_is_streaming(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    long is_streaming;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    is_streaming = Confsec_ResponseIsStreaming(handle, &err);
    HANDLE_ERROR(err);

    return PyBool_FromLong(is_streaming);
}

PyObject* py_confsec_response_get_body(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    char* body;
    PyObject* py_body;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    body = Confsec_ResponseGetBody(handle, &err);
    HANDLE_ERROR(err);

    // In general, we expect an error to be returned if the body is NULL, but we
    // should check just in case and throw an exception if it is.
    if (body == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Unexpected error getting request body");
        return NULL;
    }

    py_body = PyBytes_FromString(body);
    // PyBytes_FromString copies the underlying string, so we should free it here to
    // avoid a memory leak.
    Confsec_Free(body);

    return py_body;
}

static PyObject* py_confsec_response_get_stream(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    uintptr_t stream_handle;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    stream_handle = Confsec_ResponseGetStream(handle, &err);
    HANDLE_ERROR(err);

    // In general, we expect an error to be returned if the stream is NULL, but we
    // should check just in case and throw an exception if it is.
    if (stream_handle == 0) {
        PyErr_SetString(PyExc_RuntimeError, "Unexpected error getting response stream");
        return NULL;
    }

    return PyLong_FromUnsignedLongLong(stream_handle);
}

static PyObject* py_confsec_response_stream_get_next(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;
    char* chunk;
    PyObject* py_chunk;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    chunk = Confsec_ResponseStreamGetNext(handle, &err);
    HANDLE_ERROR(err);

    if (chunk == NULL) {
        PyErr_SetString(PyExc_StopIteration, "No more chunks");
        return NULL;
    }

    py_chunk = PyBytes_FromString(chunk);
    // PyBytes_FromString copies the underlying string, so we should free it here to
    // avoid a memory leak.
    Confsec_Free(chunk);

    return py_chunk;
}

static PyObject* py_confsec_response_stream_destroy(PyObject* self, PyObject* args) {
    INIT_ERROR;
    uintptr_t handle;

    if (!PyArg_ParseTuple(args, "K", &handle)) {
        return NULL;
    }

    Confsec_ResponseStreamDestroy(handle, &err);
    HANDLE_ERROR(err);

    Py_RETURN_NONE;
}

static PyMethodDef LibconfsecPyMethods[] = {
    {"confsec_client_create", py_confsec_client_create, METH_VARARGS, "Create a Confsec client"},
    {"confsec_client_destroy", py_confsec_client_destroy, METH_VARARGS, "Destroy a Confsec client"},
    {"confsec_client_get_default_credit_amount_per_request", py_confsec_client_get_default_credit_amount, METH_VARARGS, "Get the default credit amount per request"},
    {"confsec_client_get_max_candidate_nodes", py_confsec_client_get_max_candidate_nodes, METH_VARARGS, "Get the maximum number of candidate nodes"},
    {"confsec_client_get_default_node_tags", py_confsec_client_get_default_node_tags, METH_VARARGS, "Get the default node tags"},
    {"confsec_client_set_default_node_tags", py_confsec_client_set_default_node_tags, METH_VARARGS, "Set the default node tags"},
    {"confsec_client_get_wallet_status", py_confsec_client_get_wallet_status, METH_VARARGS, "Get the wallet status"},
    {"confsec_client_do_request", py_confsec_client_do_request, METH_VARARGS, "Perform a request"},
    {"confsec_response_destroy", py_confsec_response_destroy, METH_VARARGS, "Destroy a response"},
    {"confsec_response_is_streaming", py_confsec_response_is_streaming, METH_VARARGS, "Check if a response is streaming"},
    {"confsec_response_get_metadata", py_confsec_response_get_metadata, METH_VARARGS, "Get the metadata of a response"},
    {"confsec_response_get_body", py_confsec_response_get_body, METH_VARARGS, "Get the body of a response"},
    {"confsec_response_get_stream", py_confsec_response_get_stream, METH_VARARGS, "Get the stream of a response"},
    {"confsec_response_stream_get_next", py_confsec_response_stream_get_next, METH_VARARGS, "Get the next chunk of a response stream"},
    {"confsec_response_stream_destroy", py_confsec_response_stream_destroy, METH_VARARGS, "Destroy a response stream"},
    {NULL, NULL, 0, NULL}
};


static struct PyModuleDef libconfsec_py_module = {
    PyModuleDef_HEAD_INIT,
    "libconfsec_py",
    "A wrapper for libconfsec",
    -1,
    LibconfsecPyMethods
};

PyMODINIT_FUNC PyInit_libconfsec_py(void) {
    return PyModule_Create(&libconfsec_py_module);
}
